from __future__ import annotations

import logging
from pathlib import Path
from typing import List

NOTES_DIR = Path(__file__).resolve().parents[2] / "data" / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)


def _slugify(title: str) -> str:
    slug = "-".join(title.lower().strip().split())
    return slug or "note"


def create_note(title: str, content: str) -> str:
    name = title.strip() or "note"
    slug = _slugify(name)
    path = NOTES_DIR / f"{slug}.txt"
    body = content.strip() if content else ""
    path.write_text(body, encoding="utf-8")
    logging.debug("Note created: %s (%s chars)", path.name, len(body))
    return f"Saved note '{name}' -> {path.name}"


def list_notes() -> List[str]:
    files = sorted(NOTES_DIR.glob("*.txt"))
    return [f.stem for f in files]


def read_note(title: str) -> str:
    name = title.strip() or "note"
    path = NOTES_DIR / f"{_slugify(name)}.txt"
    if not path.exists():
        return f"Note '{name}' not found"
    content = path.read_text(encoding="utf-8")
    logging.debug("Note read: %s (%s chars)", path.name, len(content))
    return content or f"Note '{name}' is empty"


def search_notes(keyword: str, limit: int = 5) -> List[str]:
    term = keyword.lower().strip()
    if not term:
        return []

    results: List[str] = []
    for file in sorted(NOTES_DIR.glob("*.txt")):
        text = file.read_text(encoding="utf-8")
        if term in text.lower() or term in file.stem.lower():
            snippet = text.strip().replace("\n", " ")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            results.append(f"{file.stem}: {snippet}")
        if len(results) >= limit:
            break
    return results


def get_note_summaries(limit: int = 3, snippet_chars: int = 120) -> List[str]:
    summaries: List[str] = []
    for file in sorted(NOTES_DIR.glob("*.txt"))[:limit]:
        text = file.read_text(encoding="utf-8").strip().replace("\n", " ")
        if len(text) > snippet_chars:
            text = text[: snippet_chars - 3] + "..."
        summaries.append(f"{file.stem}: {text}")
    return summaries
