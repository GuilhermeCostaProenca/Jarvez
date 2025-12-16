from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, List

from jarvez.mood import detector
from jarvez.mood.store import MoodStore
from jarvez.rag.retriever import Retriever
from jarvez.storage.db import JarvezDatabase

DB = JarvezDatabase()


def create_entry(text: str, retriever: Retriever | None = None, mood_store: MoodStore | None = None) -> str:
    entry_id = f"journal-{int(datetime.utcnow().timestamp())}"
    timestamp = datetime.utcnow().isoformat() + "Z"
    text_clean = text.strip()
    DB.add_journal_entry(entry_id, content=text_clean, created_at=timestamp)

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

    return "Journal registrado"


def summarize(period: str = "week") -> str:
    entries = DB.list_journal_entries(limit=30 if period == "month" else 7)
    texts: List[str] = [e.get("content", "") for e in entries]
    if not texts:
        return "Nenhum journal registrado."
    # simple heuristic summary stub
    joined = " ".join(texts)
    return f"[journal stub] {len(texts)} entradas analisadas. Temas recorrentes precisam de sumarizador real. Trechos: {joined[:300]}"
