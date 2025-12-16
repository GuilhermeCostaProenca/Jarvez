from __future__ import annotations

import asyncio
import time
from typing import Optional

import psutil

from jarvez.sensors.bus import EventBus


def _detect_media() -> Optional[str]:
    for proc in psutil.process_iter(["name", "cmdline"]):
        name = (proc.info.get("name") or "").lower()
        if "spotify" in name:
            return "Spotify (heuristic)"
        if "vlc" in name:
            return "VLC"
        if "youtube" in " ".join(proc.info.get("cmdline") or []).lower():
            return "YouTube (browser)"
    return None


async def watch_media(bus: EventBus, interval: float = 6.0) -> None:
    last = None
    while True:
        media = _detect_media()
        if media != last:
            await bus.publish({"type": "media_now_playing", "ts": time.time(), "payload": {"title": media}, "source": "sensor.media"})
            last = media
        await asyncio.sleep(interval)
