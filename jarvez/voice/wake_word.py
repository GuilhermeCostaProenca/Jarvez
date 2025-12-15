from __future__ import annotations

import logging
import os
import queue
import threading
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

try:
    import pvporcupine
except Exception:
    pvporcupine = None


@dataclass
class WakeWordConfig:
    wake_word: str = "jarvez"
    device: Optional[int | str] = None
    cooldown_seconds: float = 3.0
    min_energy_ms: float = 300.0  # require this much voiced energy before accepting a wake
    energy_threshold: float = 350.0  # raw int16 mean absolute amplitude threshold


class WakeWordDetector:
    """
    Wake word detector with Porcupine when available, falling back to simple energy gating.
    The detector enforces a cooldown and a minimum energy window to reduce false triggers.
    """

    def __init__(self, config: WakeWordConfig, debug: bool = False):
        self.config = config
        self.debug = debug or os.environ.get("JARVEZ_DEBUG") == "1"
        self._q: queue.Queue[bytes] = queue.Queue()
        self._porcupine = self._init_porcupine()
        self.sample_rate = self._porcupine.sample_rate if self._porcupine else 16000
        # Use Porcupine's frame length if present; otherwise 30 ms frames for VAD-like gating.
        self.frame_length = self._porcupine.frame_length if self._porcupine else int(self.sample_rate * 0.03)
        self._last_trigger = 0.0

    def _init_porcupine(self):
        if not pvporcupine:
            if self.debug:
                logging.debug("Porcupine not installed; falling back to energy-based wake detection.")
            return None

        access_key = (
            os.environ.get("PV_ACCESS_KEY")
            or os.environ.get("PORCUPINE_ACCESS_KEY")
            or os.environ.get("PICOVOICE_API_KEY")
        )
        if not access_key:
            logging.info("Porcupine available but no access key set; using energy-based wake detection.")
            return None

        keyword = (self.config.wake_word or "jarvez").lower()
        available = getattr(pvporcupine, "KEYWORDS", [])
        # Porcupine ships "jarvis" but not "jarvez"; use jarvis as default and allow override via path/available keyword.
        keyword_list = [keyword] if keyword in available else ["jarvis"]
        keyword_paths = None
        custom_path = os.environ.get("JARVEZ_WAKE_WORD_PATH")
        if custom_path and os.path.exists(custom_path):
            keyword_paths = [custom_path]
            keyword_list = None
        try:
            porcupine = pvporcupine.create(
                access_key=access_key,
                keywords=keyword_list if keyword_list else None,
                keyword_paths=keyword_paths,
            )
            logging.info("Porcupine wake word enabled (%s).", keyword_list[0] if keyword_list else "custom")
            return porcupine
        except Exception as exc:
            logging.warning("Failed to init Porcupine (%s); falling back to energy-based wake detection.", exc)
            return None

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logging.debug("Audio status: %s", status)
        # indata is numpy array; copy to avoid referencing buffer reused by sounddevice
        self._q.put(indata.copy().tobytes())

    def wait_for_wake(self, stop_event: Optional[threading.Event] = None) -> bool:
        if not sd:
            logging.warning("sounddevice not installed; wake detection disabled.")
            time.sleep(1.0)
            return False

        min_energy_frames = max(1, int((self.config.min_energy_ms / 1000.0) / (self.frame_length / self.sample_rate)))
        speech_frames = 0

        with sd.InputStream(
            samplerate=self.sample_rate,
            blocksize=self.frame_length,
            device=self.config.device,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while True:
                if stop_event and stop_event.is_set():
                    return False
                try:
                    chunk: bytes = self._q.get(timeout=0.2)
                except queue.Empty:
                    continue

                pcm = np.frombuffer(chunk, dtype=np.int16)
                energy = float(np.abs(pcm).mean())
                voiced = energy > self.config.energy_threshold
                speech_frames = speech_frames + 1 if voiced else 0

                if self._porcupine:
                    result = self._porcupine.process(pcm)
                    if self.debug:
                        logging.debug("wake energy=%.1f frames=%s result=%s", energy, speech_frames, result)
                    if result >= 0 and speech_frames >= min_energy_frames and self._cooldown_ok():
                        self._mark_trigger()
                        return True
                else:
                    # Energy-only fallback: require sustained voiced frames
                    if speech_frames >= min_energy_frames and self._cooldown_ok():
                        if self.debug:
                            logging.debug("wake (energy fallback) energy=%.1f frames=%s", energy, speech_frames)
                        self._mark_trigger()
                        return True

    def _cooldown_ok(self) -> bool:
        return (time.time() - self._last_trigger) >= self.config.cooldown_seconds

    def _mark_trigger(self) -> None:
        self._last_trigger = time.time()


def _main():
    import argparse

    parser = argparse.ArgumentParser(description="Jarvez wake word debug listener")
    parser.add_argument("--device", type=str, default=None, help="sounddevice input device id/name")
    parser.add_argument("--debug", action="store_true", help="verbose logging")
    args = parser.parse_args()

    if sd is None:
        print("sounddevice not installed; wake test unavailable.")
        return

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    cfg = WakeWordConfig(device=args.device)
    detector = WakeWordDetector(cfg, debug=args.debug)
    stop_event = threading.Event()
    print("Listening for wake word. Ctrl+C to stop.")
    try:
        while True:
            detected = detector.wait_for_wake(stop_event)
            if not detected:
                break
            print("wake detected")
    except KeyboardInterrupt:
        stop_event.set()
        print("\nStopped.")


if __name__ == "__main__":
    _main()
