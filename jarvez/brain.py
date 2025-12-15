from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
import time
from typing import Any, Dict, Set

import websockets
from dotenv import load_dotenv

from jarvez.core.agent import Agent
from jarvez.voice.voice_loop import VoiceLoop

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

# Load environment variables from .env early so downstream clients (OpenAI, etc.) are configured.
load_dotenv()

STATE: Dict[str, Any] = {
    "state": "idle",      # idle | listening | thinking | speaking | intense
    "intensity": 0.25,    # 0.0 - 1.2
    "mood": "calm",       # calm | focus | warm | alert | etc
}

CLIENTS: Set[websockets.WebSocketServerProtocol] = set()
AGENT: Agent | None = None
VOICE_THREAD: threading.Thread | None = None
VOICE_LOOP: VoiceLoop | None = None


def start_agent() -> None:
    global AGENT
    # This spins up the mind; further hooks (mood, planner, awareness) can update STATE later.
    AGENT = Agent()


def set_state(state: str, intensity: float | None = None, mood: str | None = None) -> None:
    STATE["state"] = state
    if intensity is not None:
        STATE["intensity"] = max(0.0, min(1.2, float(intensity)))
    if mood:
        STATE["mood"] = mood


def start_voice_loop() -> None:
    global VOICE_LOOP, VOICE_THREAD
    enabled = os.environ.get("JARVEZ_VOICE_ENABLED", "1") == "1"
    if not enabled:
        logging.info("Voice loop disabled (JARVEZ_VOICE_ENABLED=0).")
        return

    def _runner() -> None:
        # Wait for the agent to be ready to service chat fallbacks
        while AGENT is None:
            time.sleep(0.1)
        try:
            VOICE_LOOP = VoiceLoop(set_state=set_state, agent=AGENT)
            VOICE_LOOP.run()
        except Exception as exc:
            logging.warning("Voice loop stopped: %s", exc)

    VOICE_THREAD = threading.Thread(target=_runner, daemon=True)
    VOICE_THREAD.start()


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
    new_state = data.get("state", STATE["state"])
    intensity = data.get("intensity", None)
    mood = data.get("mood", None)
    set_state(str(new_state).lower(), intensity, str(mood).lower() if mood else None)


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
    logging.basicConfig(level=logging.DEBUG if os.environ.get("JARVEZ_DEBUG") == "1" else logging.INFO)
    threading.Thread(target=start_agent, daemon=True).start()
    start_voice_loop()
    asyncio.run(serve())


if __name__ == "__main__":
    main()
