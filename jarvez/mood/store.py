from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

DEFAULT_MOOD_PATH = Path(__file__).resolve().parents[2] / "data" / "mood_trace.json"


class MoodStore:
    def __init__(self, path: Path | str = DEFAULT_MOOD_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: List[Dict] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8-sig"))
            except Exception as exc:
                logging.error("Failed to load mood trace: %s", exc)
                self._data = []
        else:
            self.save()

    def save(self) -> None:
        self.path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def append(self, mood: Dict) -> None:
        self._data.append(mood)
        self.save()

    def recent(self, limit: int = 5) -> List[Dict]:
        return list(self._data[-limit:])
