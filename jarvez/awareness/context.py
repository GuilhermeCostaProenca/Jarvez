from __future__ import annotations

import time
from typing import Dict, Optional

from jarvez.awareness.detectors import active_app, detect_context, idle_detector


class AwarenessContext:
    def __init__(self):
        self.active_app: Dict[str, Optional[str]] = {}
        self.context_type: str = "idle"
        self.last_change: float = time.time()
        self.last_activity: float = time.time()

    def update_from_system(self) -> Dict[str, str]:
        app = active_app()
        ctx = detect_context(app)
        changed = ctx != self.context_type
        if changed:
            self.context_type = ctx
            self.active_app = app
            self.last_change = time.time()
        self.last_activity = time.time()
        return {
            "context": self.context_type,
            "process": app.get("process"),
            "title": app.get("title"),
            "changed": changed,
            "timestamp": self.last_change,
        }

    def check_idle(self, threshold: int = 900) -> Optional[Dict[str, str]]:
        if idle_detector(self.last_activity, threshold):
            if self.context_type != "idle":
                self.context_type = "idle"
                self.last_change = time.time()
                return {"context": "idle", "process": None, "title": None, "changed": True, "timestamp": self.last_change}
        return None
