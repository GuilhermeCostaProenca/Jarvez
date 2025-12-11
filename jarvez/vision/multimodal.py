from __future__ import annotations

import base64
import logging
import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _provider_client() -> Optional[OpenAI]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if OpenAI and api_key:
        try:
            return OpenAI(api_key=api_key)
        except Exception as exc:
            logging.error("Failed to init OpenAI client for vision: %s", exc)
    return None


def analyze_image(image_bytes: bytes, prompt: str, mode: str | None = None) -> str:
    """
    Analyze an image with an optional provider; fallback to stub.
    """
    client = _provider_client()
    if client:
        try:
            encoded = base64.b64encode(image_bytes).decode("utf-8")
            response = client.chat.completions.create(
                model=os.environ.get("JARVEZ_VISION_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": f"Mode: {mode or 'vision'}"},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}},
                        ],
                    },
                ],
            )
            text = response.choices[0].message.content
            return text or "[vision] empty response"
        except Exception as exc:
            logging.error("Vision provider failed: %s", exc)

    logging.info("[vision stub] prompt=%s bytes=%s mode=%s", prompt[:60], len(image_bytes), mode)
    return "[vision stub] Nenhum provedor configurado; simulando analise."
