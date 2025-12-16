from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "jarvez.db"
DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class JarvezDatabase:
    """SQLite-backed storage for events, memories, notes, and RAG chunks.

    The database is created lazily at the default path (data/jarvez.db).
    A one-shot migration will import legacy JSON files under data/*.
    """

    def __init__(self, path: str | Path | None = None, data_dir: str | Path = DEFAULT_DATA_DIR):
        db_path = Path(os.environ.get("JARVEZ_DB_PATH", path or DEFAULT_DB_PATH))
        self.path = db_path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.data_dir = Path(data_dir)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()
        self._maybe_migrate_legacy()

    # ------------------------------------------------------------------
    # Schema and migration
    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                payload TEXT,
                source TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                text TEXT NOT NULL,
                tags TEXT,
                importance REAL,
                source TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                expires_at TEXT,
                privacy_level TEXT DEFAULT 'default',
                section TEXT DEFAULT 'facts',
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                tags TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT,
                source TEXT
            );
            CREATE TABLE IF NOT EXISTS plans (
                id TEXT PRIMARY KEY,
                goal TEXT,
                deadline TEXT,
                steps TEXT,
                status TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS journal_entries (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                mood TEXT,
                tags TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS mood_trace (
                id TEXT PRIMARY KEY,
                sentiment TEXT,
                score REAL,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                metadata TEXT
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS deletions_audit (
                id TEXT PRIMARY KEY,
                target_type TEXT,
                target_id TEXT,
                content_hash TEXT,
                deleted_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE TABLE IF NOT EXISTS rag_chunks (
                id TEXT PRIMARY KEY,
                text TEXT,
                metadata TEXT,
                embedding TEXT,
                created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            );
            CREATE INDEX IF NOT EXISTS idx_events_created_at ON events (created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_memories_created_at ON memories (created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_notes_created_at ON notes (created_at DESC);
            CREATE INDEX IF NOT EXISTS idx_rag_chunks_created_at ON rag_chunks (created_at DESC);
            """
        )
        self.conn.commit()

    def _maybe_migrate_legacy(self) -> None:
        migrated = self.get_setting("legacy_migrated")
        if migrated == "1":
            return
        try:
            self._migrate_memory_json()
            self._migrate_planner_json()
            self._migrate_mood_trace()
            self._migrate_telemetry()
            self._migrate_rag_index()
            self._migrate_notes_dir()
            self.upsert_setting("legacy_migrated", "1")
        except Exception as exc:
            logging.warning("Legacy migration failed: %s", exc)

    def _migrate_memory_json(self) -> None:
        path = self.data_dir / "memory.json"
        if not path.exists():
            return
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        user = raw.get("user")
        if user:
            self.upsert_setting("user_profile", json.dumps(user))
        state = raw.get("state", {})
        if state.get("last_mode"):
            self.upsert_setting("last_mode", state.get("last_mode"))

        facts = raw.get("facts", [])
        dynamics = raw.get("dynamic_facts", [])
        for item in list(facts) + list(dynamics):
            mem_id = item.get("id") or f"mem-{item.get('timestamp', _utcnow())}"
            tags = item.get("tags") or ([] if not item.get("type") else [item["type"]])
            self.upsert_memory(
                mem_id,
                text=item.get("content", ""),
                tags=tags,
                source=item.get("source", "memory.json"),
                created_at=item.get("timestamp"),
                section="dynamic_facts" if item in dynamics else "facts",
                metadata={k: v for k, v in item.items() if k not in {"id", "content", "tags", "timestamp", "source"}},
            )

    def _migrate_planner_json(self) -> None:
        path = self.data_dir / "planner.json"
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for plan in payload.get("plans", []):
            self.upsert_plan(
                plan.get("id") or f"plan-{_utcnow()}",
                goal=plan.get("goal", ""),
                deadline=plan.get("deadline"),
                steps=plan.get("steps", []),
                status=plan.get("status", "open"),
                created_at=plan.get("created_at"),
                updated_at=plan.get("updated_at"),
            )

    def _migrate_mood_trace(self) -> None:
        path = self.data_dir / "mood_trace.json"
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload:
            mood_id = item.get("id") or f"mood-{_utcnow()}"
            self.add_mood({"id": mood_id, **{k: v for k, v in item.items() if k != "id"}})

    def _migrate_telemetry(self) -> None:
        path = self.data_dir / "telemetry.log.jsonl"
        if not path.exists():
            return
        with path.open("r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    self.add_event(
                        record.get("id"),
                        record.get("type", "event"),
                        payload=record.get("payload"),
                        created_at=record.get("ts"),
                        source="telemetry.log",
                    )
                except Exception:
                    continue

    def _migrate_rag_index(self) -> None:
        path = self.data_dir / "rag_index.json"
        if not path.exists():
            return
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        for item in payload:
            self.upsert_rag_chunk(
                item.get("doc_id"),
                text=item.get("text", ""),
                metadata=item.get("metadata", {}),
                embedding=item.get("embedding", {}),
            )

    def _migrate_notes_dir(self) -> None:
        notes_dir = self.data_dir / "notes"
        if not notes_dir.exists():
            return
        for note_file in notes_dir.glob("*.txt"):
            content = note_file.read_text(encoding="utf-8-sig")
            note_id = note_file.stem
            self.upsert_note(
                note_id,
                title=note_file.stem,
                content=content,
                source="notes_dir",
                created_at=_utcnow(),
            )

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def get_setting(self, key: str) -> Optional[str]:
        cur = self.conn.cursor()
        row = cur.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    def upsert_setting(self, key: str, value: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO settings(key, value, updated_at) VALUES(?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
            """,
            (key, value, _utcnow()),
        )
        self.conn.commit()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def add_event(
        self,
        event_id: Optional[str],
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> str:
        eid = event_id or f"evt-{_utcnow()}"
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO events(id, type, payload, source, created_at) VALUES (?, ?, ?, ?, ?)",
            (eid, event_type, json.dumps(payload or {}), source, created_at or _utcnow()),
        )
        self.conn.commit()
        return eid

    def recent_events(self, limit: int = 50, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if event_type:
            rows = cur.execute(
                "SELECT * FROM events WHERE type = ? ORDER BY created_at DESC LIMIT ?",
                (event_type, limit),
            ).fetchall()
        else:
            rows = cur.execute("SELECT * FROM events ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Memories
    # ------------------------------------------------------------------
    def upsert_memory(
        self,
        mem_id: str,
        text: str,
        tags: Optional[Sequence[str]] = None,
        importance: Optional[float] = None,
        source: Optional[str] = None,
        created_at: Optional[str] = None,
        expires_at: Optional[str] = None,
        privacy_level: Optional[str] = None,
        section: str = "facts",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO memories(id, text, tags, importance, source, created_at, expires_at, privacy_level, section, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                mem_id,
                text,
                json.dumps(list(tags) if tags else []),
                importance,
                source,
                created_at or _utcnow(),
                expires_at,
                privacy_level or "default",
                section,
                json.dumps(metadata or {}),
            ),
        )
        self.conn.commit()

    def search_memories(self, query: Optional[str] = None, limit: int = 20, section: Optional[str] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        sql = "SELECT * FROM memories"
        clauses: List[str] = []
        params: List[Any] = []
        if query:
            clauses.append("LOWER(text) LIKE ?")
            params.append(f"%{query.lower()}%")
        if section:
            clauses.append("section = ?")
            params.append(section)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = cur.execute(sql, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Notes
    # ------------------------------------------------------------------
    def upsert_note(
        self,
        note_id: str,
        title: Optional[str],
        content: str,
        tags: Optional[Sequence[str]] = None,
        source: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO notes(id, title, content, tags, created_at, updated_at, source) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                note_id,
                title,
                content,
                json.dumps(list(tags) if tags else []),
                created_at or _utcnow(),
                _utcnow(),
                source,
            ),
        )
        self.conn.commit()

    def list_notes(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.conn.cursor().execute(
            "SELECT * FROM notes ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def get_note(self, note_id: str) -> Optional[Dict[str, Any]]:
        row = self.conn.cursor().execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    # ------------------------------------------------------------------
    # Plans
    # ------------------------------------------------------------------
    def upsert_plan(
        self,
        plan_id: str,
        goal: str,
        deadline: Optional[str],
        steps: Sequence[str],
        status: str,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO plans(id, goal, deadline, steps, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (plan_id, goal, deadline, json.dumps(list(steps)), status, created_at or _utcnow(), updated_at or _utcnow()),
        )
        self.conn.commit()

    def list_plans(self) -> List[Dict[str, Any]]:
        rows = self.conn.cursor().execute("SELECT * FROM plans ORDER BY created_at DESC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Mood
    # ------------------------------------------------------------------
    def add_mood(self, mood: Dict[str, Any]) -> None:
        mood_id = mood.get("id") or f"mood-{_utcnow()}"
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO mood_trace(id, sentiment, score, created_at, metadata) VALUES (?, ?, ?, ?, ?)",
            (mood_id, mood.get("sentiment"), mood.get("score"), mood.get("created_at") or _utcnow(), json.dumps({k: v for k, v in mood.items() if k not in {"id", "sentiment", "score", "created_at"}})),
        )
        self.conn.commit()

    def recent_mood(self, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self.conn.cursor().execute("SELECT * FROM mood_trace ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Journal
    # ------------------------------------------------------------------
    def add_journal_entry(
        self,
        entry_id: str,
        content: str,
        title: Optional[str] = None,
        mood: Optional[str] = None,
        tags: Optional[Sequence[str]] = None,
        created_at: Optional[str] = None,
    ) -> None:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO journal_entries(id, title, content, mood, tags, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (entry_id, title, content, mood, json.dumps(list(tags) if tags else []), created_at or _utcnow()),
        )
        self.conn.commit()

    def list_journal_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self.conn.cursor().execute("SELECT * FROM journal_entries ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [self._row_to_dict(r) for r in rows]

    # ------------------------------------------------------------------
    # RAG chunks
    # ------------------------------------------------------------------
    def upsert_rag_chunk(self, chunk_id: str, text: str, metadata: Dict[str, Any], embedding: Dict[str, Any]) -> None:
        if not chunk_id:
            chunk_id = f"rag-{_utcnow()}"
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO rag_chunks(id, text, metadata, embedding, created_at)
            VALUES (?, ?, ?, ?, COALESCE((SELECT created_at FROM rag_chunks WHERE id = ?), ?))
            """,
            (chunk_id, text, json.dumps(metadata), json.dumps(embedding), chunk_id, _utcnow()),
        )
        self.conn.commit()

    def all_rag_chunks(self) -> List[Dict[str, Any]]:
        rows = self.conn.cursor().execute("SELECT * FROM rag_chunks").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def delete_rag_chunks(self, ids: Iterable[str]) -> None:
        ids = list(ids)
        if not ids:
            return
        cur = self.conn.cursor()
        cur.executemany("DELETE FROM rag_chunks WHERE id = ?", [(i,) for i in ids])
        self.conn.commit()

    # ------------------------------------------------------------------
    # Forget pipeline
    # ------------------------------------------------------------------
    def forget(self, query: Optional[str] = None, ids: Optional[List[str]] = None) -> Dict[str, int]:
        ids = ids or []
        stats = {"events": 0, "memories": 0, "notes": 0, "plans": 0, "journal": 0, "mood": 0, "rag": 0}
        if not query and not ids:
            return stats
        cur = self.conn.cursor()

        def _record_audit(target_type: str, target_id: str, content_sample: Optional[str]) -> None:
            digest = hashlib.sha256((content_sample or target_id).encode("utf-8", errors="ignore")).hexdigest()
            cur.execute(
                "INSERT OR REPLACE INTO deletions_audit(id, target_type, target_id, content_hash, deleted_at) VALUES (?, ?, ?, ?, ?)",
                (f"del-{target_type}-{target_id}", target_type, target_id, digest, _utcnow()),
            )

        def _delete(table: str, id_field: str, body_field: str) -> int:
            rows = cur.execute(f"SELECT {id_field}, {body_field} FROM {table}").fetchall()
            matched = []
            for row in rows:
                rid = row[0]
                body = row[1] or ""
                match = False
                if ids and rid in ids:
                    match = True
                if query and query.lower() in str(body).lower():
                    match = True
                if not match:
                    continue
                matched.append((rid, body))
            for rid, body in matched:
                _record_audit(table, rid, str(body))
                cur.execute(f"DELETE FROM {table} WHERE {id_field} = ?", (rid,))
            return len(matched)

        stats["memories"] = _delete("memories", "id", "text")
        stats["notes"] = _delete("notes", "id", "content")
        stats["plans"] = _delete("plans", "id", "goal")
        stats["journal"] = _delete("journal_entries", "id", "content")
        stats["mood"] = _delete("mood_trace", "id", "sentiment")
        stats["events"] = _delete("events", "id", "payload")
        stats["rag"] = _delete("rag_chunks", "id", "text")
        self.conn.commit()
        return stats

    # ------------------------------------------------------------------
    def _row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        data = dict(row)
        for key in ("payload", "metadata", "tags", "steps", "embedding"):
            if key in data and isinstance(data[key], str):
                try:
                    data[key] = json.loads(data[key])
                except Exception:
                    pass
        return data
