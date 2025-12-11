from __future__ import annotations

import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

from jarvez.config import load_config

try:
    from PIL import ImageGrab  # type: ignore
except Exception:
    ImageGrab = None


def capture_screen(save: bool = False) -> Tuple[bytes, Optional[Path]]:
    """
    Capture full screen. Returns image bytes and optional saved path.
    Falls back to stub when not permitted or not supported.
    """
    cfg = load_config()
    if not cfg.vision_enabled or not cfg.vision_allow_screen:
        logging.info("Vision screen capture disabled by config.")
        return b"", None

    if ImageGrab is None:
        logging.info("PIL.ImageGrab not available; returning stub capture.")
        return b"", None

    try:
        img = ImageGrab.grab()
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        data = buffer.getvalue()
        path = None
        if save:
            capture_dir = Path(cfg.paths.default_capture_dir)
            capture_dir.mkdir(parents=True, exist_ok=True)
            path = capture_dir / f"screen-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.png"
            path.write_bytes(data)
        return data, path
    except Exception as exc:
        logging.error("Screen capture failed: %s", exc)
        return b"", None
