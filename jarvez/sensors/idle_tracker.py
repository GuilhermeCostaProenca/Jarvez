from __future__ import annotations

import asyncio
import time

import psutil

from jarvez.sensors.bus import EventBus


async def watch_idle_time(bus: EventBus, interval: float = 5.0, activity_threshold: float = 5.0) -> None:
    """Approximate idle time based on CPU usage when OS-level hooks are unavailable."""
    idle_seconds = 0.0
    while True:
        cpu = psutil.cpu_percent(interval=0.1)
        if cpu < activity_threshold:
            idle_seconds += interval
        else:
            idle_seconds = 0.0
        await bus.publish({"type": "idle_status", "ts": time.time(), "payload": {"idle_seconds": idle_seconds}, "source": "sensor.idle"})
        await asyncio.sleep(interval)
