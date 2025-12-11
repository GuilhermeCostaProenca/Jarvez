from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from jarvez.mood import detector
from jarvez.mood.store import MoodStore
from jarvez.rag.retriever import Retriever

JOURNAL_DIR = Path(__file__).resolve().parents[2] / "data" / "journal"
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)


def _journal_path() -> Path:
    return JOURNAL_DIR / f"{datetime.utcnow().date().isoformat()}.json"


def create_entry(text: str, retriever: Retriever | None = None, mood_store: MoodStore | None = None) -> str:
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "text": text.strip(),
    }
    path = _journal_path()
    data: List[Dict] = []
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            data = []
    data.append(entry)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    mood_trace = detector.detect_mood(text)
    if mood_store:
        mood_store.append(mood_trace)

    if retriever:
        try:
            retriever.index_document(
                doc_id=f"journal-{entry['timestamp']}",
                text=entry["text"],
                metadata={"type": "journal", "date": str(datetime.utcnow().date())},
            )
        except Exception as exc:
            logging.debug("Failed to index journal entry: %s", exc)

    return f"Journal registrado em {path.name}"


def summarize(period: str = "week") -> str:
    files = sorted(JOURNAL_DIR.glob("*.json"))
    if not files:
        return "Nenhum journal registrado."
    # naive: read recent files
    recent_files = files[-7:] if period == "week" else files[-30:]
    texts: List[str] = []
    for file in recent_files:
        try:
            entries = json.loads(file.read_text(encoding="utf-8"))
            for e in entries:
                texts.append(e.get("text", ""))
        except Exception:
            continue
    if not texts:
        return "Nenhum journal registrado."
    # simple heuristic summary stub
    joined = " ".join(texts)
    return f"[journal stub] {len(texts)} entradas analisadas. Temas recorrentes precisam de sumarizador real. Trechos: {joined[:300]}"
