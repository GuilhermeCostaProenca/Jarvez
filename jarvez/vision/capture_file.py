from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from jarvez.vision import ocr


def load_file(path: str | Path) -> Optional[str]:
    file_path = Path(path)
    if not file_path.exists():
        logging.error("File not found for vision: %s", file_path)
        return None
    if file_path.suffix.lower() in {".txt", ".md"}:
        try:
            return file_path.read_text(encoding="utf-8-sig")
        except Exception as exc:
            logging.error("Failed to read text file: %s", exc)
            return None
    # for PDFs/images fallback to OCR module
    return ocr.extract_text(file_path)
