from __future__ import annotations

import asyncio
import time
from typing import Dict

import psutil

from jarvez.sensors.bus import EventBus


def _active_editor() -> str | None:
    for proc in psutil.process_iter(["name"]):
        name = (proc.info.get("name") or "").lower()
        if any(editor in name for editor in ("code", "cursor", "idea", "notepad")):
            return name
    return None


async def watch_typing(bus: EventBus, interval: float = 8.0, raw_enabled: bool | None = None) -> None:
    """Publish coarse typing activity; never captures raw text unless explicitly allowed."""
    typed_counter = 0
    allow_raw = raw_enabled if raw_enabled is not None else False
    while True:
        editor = _active_editor()
        typed_counter += 5  # simple heartbeat counter
        payload: Dict[str, object] = {
            "editor": editor,
            "keystrokes": typed_counter,
            "raw_captured": False,
        }
        if allow_raw:
            payload["raw_preview"] = "(raw text capture disabled by default)"
        await bus.publish({"type": "typing_activity", "ts": time.time(), "payload": payload, "source": "sensor.typing"})
        await asyncio.sleep(interval)
