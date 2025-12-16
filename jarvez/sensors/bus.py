from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Dict, List


SensorCallback = Callable[[Dict], Awaitable[None] | None]


class EventBus:
    """Lightweight async event bus for sensors -> consumers."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[Dict] = asyncio.Queue()
        self.subscribers: List[SensorCallback] = []
        self._task: asyncio.Task | None = None

    def subscribe(self, callback: SensorCallback) -> None:
        self.subscribers.append(callback)

    async def publish(self, event: Dict) -> None:
        await self.queue.put(event)

    async def _dispatch(self) -> None:
        while True:
            event = await self.queue.get()
            for cb in list(self.subscribers):
                try:
                    result = cb(event)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception as exc:  # pragma: no cover - safety net
                    logging.debug("Sensor subscriber failed: %s", exc)

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._dispatch())


async def start_all(bus: EventBus, watchers: List[Callable[[EventBus], Awaitable[None]]]) -> None:
    """Start all sensor coroutines and the dispatcher."""
    bus.start()
    await asyncio.gather(*(watcher(bus) for watcher in watchers))
