from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import Any, Dict, Set

import websockets

from jarvez.core.agent import Agent

"""
Jarvez brain entrypoint:
- Boots the Agent (mind)
- Exposes a local WebSocket at ws://127.0.0.1:8787
- Maintains and broadcasts live state to any body client (Godot orb)
- Accepts incoming JSON updates to change the state (e.g., from internal modules)
"""

WS_HOST = "127.0.0.1"
WS_PORT = 8787
BROADCAST_HZ = 20  # 50 ms cadence

STATE: Dict[str, Any] = {
    "state": "idle",      # idle | listening | thinking | speaking | intense
    "intensity": 0.5,     # 0.0 - 1.2
    "mood": "calm",       # calm | focus | warm | alert | etc
}

CLIENTS: Set[websockets.WebSocketServerProtocol] = set()
AGENT: Agent | None = None


def start_agent() -> None:
    global AGENT
    # This spins up the mind; further hooks (mood, planner, awareness) can update STATE later.
    AGENT = Agent()


async def handle_ws(websocket: websockets.WebSocketServerProtocol) -> None:
    CLIENTS.add(websocket)
    try:
        # Send immediate snapshot on connect
        await websocket.send(json.dumps(STATE))
        async for message in websocket:
            _ingest_message(message)
    except Exception:
        pass
    finally:
        CLIENTS.discard(websocket)


def _ingest_message(message: str) -> None:
    """Optional inbound control: allow external updates to the shared STATE."""
    try:
        data = json.loads(message)
        if not isinstance(data, dict):
            return
    except Exception:
        return
    if "state" in data:
        STATE["state"] = str(data["state"]).lower()
    if "intensity" in data:
        try:
            STATE["intensity"] = max(0.0, min(1.2, float(data["intensity"])))
        except Exception:
            pass
    if "mood" in data:
        STATE["mood"] = str(data["mood"]).lower()


async def broadcast_loop() -> None:
    while True:
        if CLIENTS:
            payload = json.dumps(STATE)
            await asyncio.gather(*(c.send(payload) for c in list(CLIENTS)), return_exceptions=True)
        await asyncio.sleep(1 / BROADCAST_HZ)


async def serve() -> None:
    async with websockets.serve(handle_ws, WS_HOST, WS_PORT, ping_interval=20, ping_timeout=10):
        logging.info("Jarvez brain WS up at ws://%s:%s", WS_HOST, WS_PORT)
        await broadcast_loop()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=start_agent, daemon=True).start()
    asyncio.run(serve())


if __name__ == "__main__":
    main()
