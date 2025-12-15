from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import webrtcvad
except Exception:
    webrtcvad = None


@dataclass
class RecorderConfig:
    sample_rate: int = 16000
    max_seconds: float = 10.0
    silence_seconds: float = 1.2
    device: Optional[int | str] = None
    energy_threshold: float = 300.0
    vad_aggressiveness: int = 2


class Recorder:
    """Capture a short utterance with basic VAD/energy-based end-of-speech detection."""

    def __init__(self, config: RecorderConfig, debug: bool = False):
        self.config = config
        self.debug = debug or os.environ.get("JARVEZ_DEBUG") == "1"
        self._vad = webrtcvad.Vad(config.vad_aggressiveness) if webrtcvad else None
        if self._vad:
            self._frame_ms = 30
        else:
            self._frame_ms = 40  # slightly longer frame for RMS fallback
        self.frame_length = int(self.config.sample_rate * (self._frame_ms / 1000.0))

    def _is_speech(self, frame: bytes) -> bool:
        if self._vad:
            try:
                return self._vad.is_speech(frame, self.config.sample_rate)
            except Exception:
                return False

        pcm = np.frombuffer(frame, dtype=np.int16)
        return float(np.abs(pcm).mean()) > self.config.energy_threshold

    def record(self, stop_event: Optional[threading.Event] = None) -> Tuple[bytes, int, Dict]:
        if not sd:
            logging.warning("sounddevice not installed; recorder disabled.")
            return b"", self.config.sample_rate, {"speech_started": False}

        frames: list[bytes] = []
        speech_started = False
        first_voice_time: Optional[float] = None
        last_voice_time: Optional[float] = None
        voiced_frames = 0
        start_time = time.time()

        def callback(indata, frames_count, time_info, status):
            nonlocal speech_started, last_voice_time
            if status:
                logging.debug("Recorder audio status: %s", status)
            pcm = indata.copy().tobytes()
            frames.append(pcm)
            if self._is_speech(pcm):
                speech_started = True
                now = time.time()
                if first_voice_time is None:
                    first_voice_time = now
                last_voice_time = now
                voiced_frames += 1

        with sd.InputStream(
            samplerate=self.config.sample_rate,
            blocksize=self.frame_length,
            device=self.config.device,
            dtype="int16",
            channels=1,
            callback=callback,
        ):
            while True:
                if stop_event and stop_event.is_set():
                    break
                now = time.time()
                if speech_started and last_voice_time and (now - last_voice_time) >= self.config.silence_seconds:
                    if self.debug:
                        logging.debug("Recorder stopped on silence %.2fs.", now - last_voice_time)
                    break
                if (now - start_time) >= self.config.max_seconds:
                    if self.debug:
                        logging.debug("Recorder hit max seconds (%.1f).", self.config.max_seconds)
                    break
                time.sleep(0.05)

        end_time = time.time()
        meta = {
            "speech_started": speech_started,
            "utterance_sec": 0.0,
            "voiced_sec": voiced_frames * (self._frame_ms / 1000.0),
            "first_voice_offset": (first_voice_time - start_time) if first_voice_time else None,
            "last_voice_offset": (last_voice_time - start_time) if last_voice_time else None,
            "record_duration": end_time - start_time,
            "start_ts": start_time,
            "end_ts": end_time,
        }

        if not speech_started:
            if self.debug:
                logging.debug("Recorder captured no speech.")
            return b"", self.config.sample_rate, meta

        audio_bytes = b"".join(frames)
        meta["utterance_sec"] = len(audio_bytes) / (self.config.sample_rate * 2)
        if meta["first_voice_offset"] is not None:
            meta["speech_start_ts"] = meta["start_ts"] + meta["first_voice_offset"]
        if meta["last_voice_offset"] is not None:
            meta["speech_end_ts"] = meta["start_ts"] + meta["last_voice_offset"]
        return audio_bytes, self.config.sample_rate, meta
