from __future__ import annotations

import argparse
import logging

from jarvez.core.agent import Agent
from jarvez.voice.audio_output import speak_text
from jarvez.backup.engine import create_backup, restore_backup
from jarvez.skills import planner
from jarvez.mood.store import MoodStore
from jarvez.config import load_config
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Jarvez CLI")
    parser.add_argument("--debug", action="store_true", help="enable debug logs and context printing")
    parser.add_argument("--mode", type=str, default=None, help="start in a specific mode (e.g., study, focus)")
    parser.add_argument("--voice", action="store_true", help="speak responses via TTS when available")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format="%(levelname)s %(message)s")
    agent = Agent(default_mode=args.mode)
    config = load_config()
    mood_store = MoodStore()

    print("Jarvez v0.9 CLI. Type 'exit' or 'quit' to leave.")
    while True:
        try:
            user_input = input("you> ").strip()
        except EOFError:
            print()
            break

        if user_input.lower() in {"exit", "quit"}:
            break

        lower = user_input.lower()
        if lower in {"status", "jarvez status"}:
            plans = planner.get_plans()
            journal_dir = Path("data/journal")
            journals = list(journal_dir.glob("*.json")) if journal_dir.exists() else []
            mood_entries = len(mood_store.recent(9999))
            print(
                f"mode={agent.orchestrator.current_mode.name} vision_enabled={config.vision_enabled} "
                f"mood_enabled={config.mood_enabled} personality={config.personality_profile} "
                f"plans={len(plans)} journals={len(journals)} mood_entries={mood_entries} "
                f"last_input={agent.last_input}"
            )
            continue

        if lower.startswith(("jarvez backup", "backup")):
            path = create_backup()
            print(f"[backup] created at {path}")
            continue

        if lower.startswith("jarvez restore") or lower.startswith("restore"):
            parts = user_input.split()
            target = parts[-1] if len(parts) >= 2 else ""
            if not target:
                print("usage: jarvez restore <backup_zip_path>")
                continue
            try:
                restore_backup(target)
                print(f"[backup] restored from {target}")
            except Exception as exc:
                print(f"[backup] restore failed: {exc}")
            continue

        response = agent.handle(user_input)
        print(f"jarvez ({response.mode})> {response.text}")

        if args.voice:
            speak_text(response.text)

        if response.skill_used:
            print(f"[skill] {response.skill_used}")
        if response.vision_used:
            print("[vision] used")
        for item in response.memory_updates:
            print(f"[memory] captured: {item[:80]}")
        if args.debug:
            if response.memory_used:
                for ctx in response.memory_context:
                    print(f"[debug] memory used: {ctx[:120]}")
            for note_line in response.note_context:
                print(f"[debug] note context: {note_line}")
            for rag_line in response.rag_context:
                print(f"[debug] rag context: {rag_line}")
            if response.mood:
                print(f"[debug] mood: {response.mood}")
            if response.personality_profile:
                print(f"[debug] personality: {response.personality_profile}")
            if response.journal_suggested:
                print("[debug] journal suggested")
            if response.event_ids:
                print(f"[debug] events: {', '.join(response.event_ids)}")

    print("Bye.")


if __name__ == "__main__":
    main()
