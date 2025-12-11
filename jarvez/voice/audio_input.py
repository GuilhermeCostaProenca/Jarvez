from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def transcribe_audio(path: str | Path, model: str = "whisper-1") -> str:
    """Transcribe an audio file using OpenAI Whisper if available; fallback to stub text."""
    path = Path(path)
    if not path.exists():
        return "Audio file not found."

    api_key = os.environ.get("OPENAI_API_KEY")
    if OpenAI and api_key:
        try:
            client = OpenAI(api_key=api_key)
            with path.open("rb") as audio_file:
                resp = client.audio.transcriptions.create(model=model, file=audio_file)
            return getattr(resp, "text", "") or ""
        except Exception as exc:
            logging.error("Whisper transcription failed: %s", exc)

    try:
        # naive text fallback: attempt to read plain text files for dev stubs
        if path.suffix.lower() in {".txt"}:
            return path.read_text(encoding="utf-8")
    except Exception as exc:
        logging.error("Fallback transcription failed: %s", exc)

    return "[voice stub] (audio transcription unavailable)"


def transcribe_text_fallback(prompt: str) -> str:
    """Return text directly; useful for environments without microphone."""
    return prompt
