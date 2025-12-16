from __future__ import annotations

from typing import Dict, List

from jarvez.storage.db import JarvezDatabase


class MoodStore:
    def __init__(self, db: JarvezDatabase | None = None):
        self.db = db or JarvezDatabase()

    def append(self, mood: Dict) -> None:
        self.db.add_mood(mood)

    def recent(self, limit: int = 5) -> List[Dict]:
        return self.db.recent_mood(limit=limit)
