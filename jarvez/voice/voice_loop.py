from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import httpx

from jarvez.voice.attention import AttentionContext, compute_attention_score
from jarvez.voice.recorder import Recorder, RecorderConfig
from jarvez.voice.transcribe import transcribe_audio
from jarvez.voice.tts import speak_text

try:
    import winsound
except Exception:
    winsound = None


class VoiceLoop:
    """Orchestrates attention-based listen -> transcribe -> chat -> speak."""

    def __init__(
        self,
        set_state: Callable[[str, float], None],
        agent=None,
    ) -> None:
        self.agent = agent
        self.set_state = set_state
        self.stop_event = threading.Event()
        self.debug = os.environ.get("JARVEZ_DEBUG") == "1"
        self.api_url = os.environ.get("JARVEZ_API_URL")
        self.api_key = os.environ.get("JARVEZ_API_KEY", "")
        self.transcribe_backend = os.environ.get("JARVEZ_TRANSCRIBE_BACKEND", "faster-whisper")

        mic_device = os.environ.get("JARVEZ_MIC_DEVICE")
        self.recorder = Recorder(RecorderConfig(device=mic_device), debug=self.debug)
        self.attention_threshold = float(os.environ.get("JARVEZ_ATTENTION_THRESHOLD", "0.75"))
        self.cooldown_seconds = float(os.environ.get("JARVEZ_ATTENTION_COOLDOWN", "3.0"))
        self.last_trigger_time = 0.0
        self.last_speech_end = time.time() - 5.0  # treat initial silence as long pause

        self.chime_path = Path(__file__).resolve().parents[2] / "assets" / "chime.wav"

    def _play_chime(self) -> None:
        if winsound and self.chime_path.exists():
            try:
                winsound.PlaySound(str(self.chime_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
            except Exception as exc:
                logging.debug("Chime playback failed: %s", exc)

    def _set_state(self, state: str, intensity: float) -> None:
        self.set_state(state, intensity)

    def _chat(self, text: str) -> Optional[str]:
        if not text:
            return None
        if self.api_url:
            try:
                headers = {"X-API-Key": self.api_key} if self.api_key else {}
                resp = httpx.post(
                    f"{self.api_url.rstrip('/')}/chat",
                    json={"message": text},
                    headers=headers,
                    timeout=30,
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("reply") or data.get("message")
            except Exception as exc:
                logging.warning("VoiceLoop chat via API failed: %s", exc)
        if self.agent:
            try:
                result = self.agent.handle(text)
                return result.text
            except Exception as exc:
                logging.warning("VoiceLoop local agent failed: %s", exc)
        return None

    def run(self) -> None:
        try:
            import sounddevice  # noqa: F401
        except Exception:
            logging.info("Voice loop disabled (sounddevice missing).")
            return

        while not self.stop_event.is_set():
            audio_bytes, sample_rate, meta = self.recorder.record(self.stop_event)
            now = time.time()

            if not meta.get("speech_started"):
                continue

            speech_start = meta.get("speech_start_ts") or meta.get("start_ts") or now
            silence_before = max(0.0, speech_start - self.last_speech_end)
            since_last_trigger = max(0.0, now - self.last_trigger_time)
            attention_ctx = AttentionContext(
                silence_before=silence_before,
                since_last_trigger=since_last_trigger,
                cooldown_seconds=self.cooldown_seconds,
            )

            transcript = transcribe_audio(audio_bytes, sample_rate, backend=self.transcribe_backend)
            if not transcript:
                self.last_speech_end = now
                continue

            score, reasons = compute_attention_score(transcript, meta, attention_ctx)
            decision = score >= self.attention_threshold and since_last_trigger >= self.cooldown_seconds
            if self.debug:
                logging.debug(
                    "attention_score=%.2f threshold=%.2f silence_before=%.2fs since_last=%.2fs decision=%s reasons=%s",
                    score,
                    self.attention_threshold,
                    silence_before,
                    since_last_trigger,
                    decision,
                    reasons,
                )

            self.last_speech_end = meta.get("speech_end_ts", now)
            if not decision:
                continue

            self.last_trigger_time = now
            self._set_state("listening", 0.55)
            self._play_chime()

            self._set_state("thinking", 0.70)
            reply = self._chat(transcript)
            if not reply:
                self._set_state("idle", 0.25)
                continue

            self._set_state("speaking", 0.85)
            speak_text(reply, voice=os.environ.get("JARVEZ_TTS_VOICE"))
            self._set_state("idle", 0.25)
            time.sleep(0.1)

    def stop(self) -> None:
        self.stop_event.set()
