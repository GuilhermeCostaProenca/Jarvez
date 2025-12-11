from __future__ import annotations

import logging
import time
from typing import Callable

from jarvez.awareness.context import AwarenessContext
from jarvez.telemetry.logger import log_event


class AwarenessLoop:
    def __init__(self, callback: Callable[[dict], None], interval: int = 5, idle_threshold: int = 900):
        self.callback = callback
        self.interval = interval
        self.idle_threshold = idle_threshold
        self.ctx = AwarenessContext()
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        while self._running:
            try:
                event = self.ctx.update_from_system()
                if event.get("changed"):
                    log_event("awareness_context_change", event)
                    self.callback(event)
                idle_evt = self.ctx.check_idle(self.idle_threshold)
                if idle_evt and idle_evt.get("changed"):
                    log_event("awareness_idle", idle_evt)
                    self.callback(idle_evt)
            except Exception as exc:
                logging.debug("Awareness loop error: %s", exc)
            time.sleep(self.interval)
