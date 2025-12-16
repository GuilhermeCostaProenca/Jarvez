from __future__ import annotations

import asyncio
import time
from typing import List

import psutil

from jarvez.sensors.bus import EventBus


def _browser_titles() -> List[str]:
    titles: List[str] = []
    for proc in psutil.process_iter(["name", "cmdline"]):
        name = (proc.info.get("name") or "").lower()
        if any(browser in name for browser in ("chrome", "edge", "firefox", "brave")):
            cmd = " ".join(proc.info.get("cmdline") or [])
            if cmd:
                titles.append(cmd[:200])
    return titles


async def watch_browser(bus: EventBus, interval: float = 5.0) -> None:
    last_snapshot: List[str] = []
    while True:
        titles = _browser_titles()
        if titles != last_snapshot:
            await bus.publish({"type": "browser_context", "ts": time.time(), "payload": {"tabs": titles[:5]}, "source": "sensor.browser"})
            last_snapshot = titles
        await asyncio.sleep(interval)
