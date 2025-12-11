from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def speak_text(text: str, voice: Optional[str] = None, model: str = "gpt-4o-mini-tts") -> str:
    """Convert text to speech when possible; otherwise return stub message."""
    api_key = os.environ.get("OPENAI_API_KEY")
    voice_id = voice or os.environ.get("JARVEZ_VOICE", "alloy")
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            speech = client.audio.speech.create(model=model, voice=voice_id, input=text)
            out_dir = Path(os.environ.get("JARVEZ_AUDIO_OUT", "data/audio"))
            out_dir.mkdir(parents=True, exist_ok=True)
            output_path = out_dir / "tts_output.mp3"
            with output_path.open("wb") as f:
                f.write(speech.read())
            return f"Audio gerado em {output_path}"
        except Exception as exc:
            logging.error("TTS failed: %s", exc)

    logging.info("[voice stub] speaking text (no audio output): %s", text[:120])
    return "[voice stub] audio not generated"
