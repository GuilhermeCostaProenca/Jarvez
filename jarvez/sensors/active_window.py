from __future__ import annotations

import asyncio
import platform
import time
from typing import Dict, Optional

import psutil

from jarvez.sensors.bus import EventBus


def _foreground_process() -> Optional[psutil.Process]:
    if platform.system() == "Windows":
        try:
            import win32gui  # type: ignore
            import win32process  # type: ignore

            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return psutil.Process(pid)
        except Exception:
            return None

    # Fallback: pick the most recently running user process
    procs = [p for p in psutil.process_iter(["name", "create_time"]) if p.info.get("name")]
    if not procs:
        return None
    return sorted(procs, key=lambda p: p.info.get("create_time", 0), reverse=True)[0]


async def watch_active_window(bus: EventBus, interval: float = 2.0) -> None:
    last_title = None
    while True:
        proc = _foreground_process()
        title = None
        name = None
        if proc:
            try:
                name = proc.name()
                title = proc.cmdline()
                if title:
                    title = " ".join(title)[:200]
            except Exception:
                name = proc.name() if proc else None
        if title != last_title:
            payload: Dict[str, str | None] = {"process": name, "title": title}
            await bus.publish({"type": "active_window", "ts": time.time(), "payload": payload, "source": "sensor.active_window"})
            last_title = title
        await asyncio.sleep(interval)
