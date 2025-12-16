import importlib
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from jarvez.storage.db import JarvezDatabase


def test_migration_json_to_sqlite(tmp_path: Path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "memory.json").write_text(
        """
        {"user": {"name": "Gui"}, "facts": [{"id": "f1", "content": "facto", "type": "fact"}], "dynamic_facts": [], "state": {"last_mode": "system"}}
        """,
        encoding="utf-8",
    )
    (data_dir / "planner.json").write_text('{"plans": [{"id": "p1", "goal": "test", "steps": []}]}', encoding="utf-8")
    (data_dir / "mood_trace.json").write_text('[{"id": "m1", "sentiment": "ok"}]', encoding="utf-8")
    (data_dir / "rag_index.json").write_text('[{"doc_id": "d1", "text": "doc", "embedding": {"vector": [], "kind": "sparse"}}]', encoding="utf-8")
    (data_dir / "telemetry.log.jsonl").write_text('{"id": "e1", "type": "evt", "payload": {}, "ts": "2024-01-01T00:00:00Z"}\n', encoding="utf-8")

    db = JarvezDatabase(path=tmp_path / "jarvez.db", data_dir=data_dir)
    assert db.get_setting("legacy_migrated") == "1"
    assert db.search_memories()
    assert db.list_plans()
    assert db.recent_mood()
    assert db.all_rag_chunks()
    assert db.recent_events()


def test_forget_pipeline_removes_records(tmp_path: Path):
    db = JarvezDatabase(path=tmp_path / "forget.db", data_dir=tmp_path)
    db.upsert_memory("mem1", text="delete me", tags=["test"], source="unit", section="facts")
    db.upsert_note("note1", title="n1", content="delete note")
    db.upsert_plan("plan1", goal="delete plan", deadline=None, steps=[], status="open")
    db.upsert_rag_chunk("rag1", text="rag delete", metadata={}, embedding={"vector": [], "kind": "sparse"})
    db.add_event("evt1", "test", payload={"text": "delete"})
    stats = db.forget(query="delete")
    assert sum(stats.values()) >= 4
    assert db.search_memories(query="delete") == []
    assert db.list_notes() == []
    assert db.list_plans() == []
    assert db.all_rag_chunks() == []


def test_timeline_insert_and_recent(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "timeline.db"
    monkeypatch.setenv("JARVEZ_DB_PATH", str(db_path))
    from jarvez.telemetry import logger, timeline

    importlib.reload(logger)
    importlib.reload(timeline)

    logger.log_event("timeline.test", {"mode": "focus"})
    events = timeline.recent(limit=5)
    assert events
    assert events[0]["type"] == "timeline.test"


def test_settings_toggle(tmp_path: Path):
    db = JarvezDatabase(path=tmp_path / "settings.db", data_dir=tmp_path)
    db.upsert_setting("raw_text", "0")
    assert db.get_setting("raw_text") == "0"
    db.upsert_setting("raw_text", "1")
    assert db.get_setting("raw_text") == "1"
    db.upsert_setting("mode", "PASSIVE_AWARE")
    assert db.get_setting("mode") == "PASSIVE_AWARE"
