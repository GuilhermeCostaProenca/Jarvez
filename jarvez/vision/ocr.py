from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def extract_text(path: str | Path) -> Optional[str]:
    """
    Minimal OCR/text extractor stub.
    - For PDF/images, returns a stub indicating extraction is not implemented unless downstream tooling is added.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    # simple text fallback for .txt/.md handled upstream
    if suffix in {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
        try:
            # placeholder for real OCR pipeline
            return f"[vision stub] OCR not configured. File: {file_path.name}"
        except Exception as exc:
            logging.error("OCR extraction failed: %s", exc)
            return None

    logging.info("Unsupported file for OCR: %s", file_path)
    return None
