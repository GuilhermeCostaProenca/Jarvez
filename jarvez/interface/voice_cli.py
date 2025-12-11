from __future__ import annotations

import argparse
import logging

from jarvez.core.agent import Agent
from jarvez.voice.microphone_loop import MicrophoneLoop


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvez voice CLI (v0.9)")
    parser.add_argument("--debug", action="store_true", help="enable debug logs and context printing")
    parser.add_argument("--tts", action="store_true", help="enable text-to-speech output when available")
    parser.add_argument("--mode", type=str, default=None, help="start in a specific mode (e.g., study, focus, planner)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s %(message)s")
    agent = Agent(default_mode=args.mode)

    loop = MicrophoneLoop(agent=agent, debug=args.debug, tts=args.tts)
    loop.run()


if __name__ == "__main__":
    main()
