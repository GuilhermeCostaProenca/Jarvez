from __future__ import annotations

import logging
from typing import Callable, Optional

from jarvez.voice.audio_input import transcribe_text_fallback
from jarvez.voice.audio_output import speak_text


class MicrophoneLoop:
    """
    Simple loop to simulate microphone-driven interaction.
    For environments without audio capture, it falls back to text input.
    """

    def __init__(self, agent, debug: bool = False, tts: bool = False) -> None:
        self.agent = agent
        self.debug = debug
        self.tts = tts

    def run(self) -> None:
        print("Jarvez voice mode (stub). Type text to simulate speech. 'exit' to quit.")
        while True:
            try:
                text = input("🎤 you (voice)> ").strip()
            except EOFError:
                print()
                break

            if text.lower() in {"exit", "quit"}:
                break

            transcript = transcribe_text_fallback(text)
            response = self.agent.handle(transcript)
            print(f"Jarvez (voice)> {response.text}")

            if self.tts:
                speak_text(response.text)

            if self.debug:
                if response.memory_used:
                    for ctx in response.memory_context:
                        print(f"[debug] memory used: {ctx[:120]}")
                for note in response.note_context:
                    print(f"[debug] note context: {note}")
                for rag in getattr(response, "rag_context", []):
                    print(f"[debug] rag context: {rag}")
                if getattr(response, "vision_used", False):
                    print("[debug] vision used")
                if getattr(response, "mood", None):
                    print(f"[debug] mood: {response.mood}")
                if getattr(response, "personality_profile", None):
                    print(f"[debug] personality: {response.personality_profile}")
                if getattr(response, "journal_suggested", False):
                    print("[debug] journal suggested")

        print("Voice loop ended.")
