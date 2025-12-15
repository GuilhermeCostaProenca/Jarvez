from __future__ import annotations

import logging
import os
import tempfile
import wave
from typing import Optional

import numpy as np

try:
    from faster_whisper import WhisperModel
except Exception:
    WhisperModel = None

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

_WHISPER_MODEL: WhisperModel | None = None


def _bytes_to_float32(audio_bytes: bytes) -> np.ndarray:
    pcm = np.frombuffer(audio_bytes, dtype=np.int16)
    return pcm.astype(np.float32) / 32768.0


def _write_temp_wav(audio_bytes: bytes, sample_rate: int) -> str:
    fd, path = tempfile.mkstemp(suffix=".wav")
    with os.fdopen(fd, "wb") as raw:
        with wave.open(raw, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes(audio_bytes)
    return path


def _ensure_local_model() -> WhisperModel | None:
    global _WHISPER_MODEL
    if _WHISPER_MODEL:
        return _WHISPER_MODEL
    if not WhisperModel:
        return None
    model_size = os.environ.get("JARVEZ_WHISPER_MODEL", "tiny")
    try:
        _WHISPER_MODEL = WhisperModel(model_size, device="cpu", compute_type="int8")
    except Exception:
        try:
            _WHISPER_MODEL = WhisperModel(model_size, device="cpu")
        except Exception as exc:
            logging.warning("Failed to init faster-whisper (%s)", exc)
            _WHISPER_MODEL = None
    return _WHISPER_MODEL


def transcribe_audio(audio_bytes: bytes, sample_rate: int, backend: Optional[str] = None) -> str:
    if not audio_bytes:
        return ""

    backend_choice = (backend or os.environ.get("JARVEZ_TRANSCRIBE_BACKEND") or "faster-whisper").lower()

    if backend_choice in {"faster-whisper", "local", "whisper"}:
        model = _ensure_local_model()
        if model:
            try:
                audio_array = _bytes_to_float32(audio_bytes)
                segments, _ = model.transcribe(audio_array, beam_size=1, language=os.environ.get("JARVEZ_WHISPER_LANG"))
                text = " ".join(seg.text.strip() for seg in segments if seg.text).strip()
                if text:
                    return text
            except Exception as exc:
                logging.warning("Local whisper transcription failed: %s", exc)

    if backend_choice == "openai" or (backend_choice == "faster-whisper" and os.environ.get("OPENAI_API_KEY")):
        if OpenAI and os.environ.get("OPENAI_API_KEY"):
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            path = _write_temp_wav(audio_bytes, sample_rate)
            try:
                with open(path, "rb") as f:
                    resp = client.audio.transcriptions.create(model="whisper-1", file=f)
                text = getattr(resp, "text", "") or ""
                if text:
                    return text
            except Exception as exc:
                logging.warning("OpenAI transcription failed: %s", exc)
            finally:
                try:
                    os.remove(path)
                except Exception:
                    pass

    logging.info("[voice stub] transcription fallback used.")
    return ""
