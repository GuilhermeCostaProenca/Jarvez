from __future__ import annotations

import logging
from typing import List

from jarvez.storage.db import JarvezDatabase

DB = JarvezDatabase()


def _slugify(title: str) -> str:
    slug = "-".join(title.lower().strip().split())
    return slug or "note"


def create_note(title: str, content: str) -> str:
    name = title.strip() or "note"
    slug = _slugify(name)
    body = content.strip() if content else ""
    DB.upsert_note(slug, title=name, content=body)
    logging.debug("Note created: %s (%s chars)", slug, len(body))
    return f"Saved note '{name}' -> {slug}"


def list_notes() -> List[str]:
    notes = DB.list_notes(limit=100)
    return [n.get("id", "") for n in notes]


def read_note(title: str) -> str:
    name = title.strip() or "note"
    note_id = _slugify(name)
    note = DB.get_note(note_id)
    if not note:
        return f"Note '{name}' not found"
    content = note.get("content", "")
    logging.debug("Note read: %s (%s chars)", note_id, len(content))
    return content or f"Note '{name}' is empty"


def search_notes(keyword: str, limit: int = 5) -> List[str]:
    term = keyword.lower().strip()
    if not term:
        return []

    results: List[str] = []
    for note in DB.list_notes(limit=200):
        text = (note.get("content") or "").lower()
        title = (note.get("title") or "").lower()
        identifier = (note.get("id") or "").lower()
        if term in text or term in title or term in identifier:
            snippet = (note.get("content") or "").strip().replace("\n", " ")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            results.append(f"{note.get('id')}: {snippet}")
        if len(results) >= limit:
            break
    return results


def get_note_summaries(limit: int = 3, snippet_chars: int = 120) -> List[str]:
    summaries: List[str] = []
    for note in DB.list_notes(limit=limit):
        text = (note.get("content") or "").strip().replace("\n", " ")
        if len(text) > snippet_chars:
            text = text[: snippet_chars - 3] + "..."
        summaries.append(f"{note.get('id')}: {text}")
    return summaries
