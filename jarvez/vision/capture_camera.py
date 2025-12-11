from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

from jarvez.config import load_config

try:
    import cv2  # type: ignore
except Exception:
    cv2 = None


def capture_frame() -> Tuple[bytes, Optional[Path]]:
    cfg = load_config()
    if not cfg.vision_enabled or not cfg.vision_allow_camera:
        logging.info("Vision camera capture disabled by config.")
        return b"", None

    if cv2 is None:
        logging.info("OpenCV not available; returning stub frame.")
        return b"", None

    try:
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            logging.error("Camera capture failed: no frame.")
            return b"", None
        success, buffer = cv2.imencode(".png", frame)
        if not success:
            logging.error("Failed to encode camera frame.")
            return b"", None
        data = buffer.tobytes()
        return data, None
    except Exception as exc:
        logging.error("Camera capture failed: %s", exc)
        return b"", None
