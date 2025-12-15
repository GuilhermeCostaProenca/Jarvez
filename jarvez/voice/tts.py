from __future__ import annotations

import logging
import os
from typing import Optional

try:
    import pyttsx3
except Exception:
    pyttsx3 = None


def speak_text(text: str, voice: Optional[str] = None, rate: Optional[int] = None) -> bool:
    """Speak text using local Windows TTS (pyttsx3). Returns True if audio played."""
    if not text:
        return False

    if pyttsx3:
        try:
            engine = pyttsx3.init()
            if voice:
                engine.setProperty("voice", voice)
            if rate:
                engine.setProperty("rate", rate)
            engine.say(text)
            engine.runAndWait()
            return True
        except Exception as exc:
            logging.warning("pyttsx3 TTS failed: %s", exc)

    logging.info("[voice stub] speak: %s", text[:120])
    return False
