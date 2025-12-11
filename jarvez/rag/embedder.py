from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import List, Sequence

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


@dataclass
class Embedding:
    vector: Sequence[float] | Sequence[str]
    kind: str  # "dense" or "sparse"


class Embedder:
    """Wrapper for embeddings with an offline sparse fallback."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        self.model = model
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if OpenAI and self.api_key else None

    def embed(self, text: str) -> Embedding:
        cleaned = text.strip()
        if not cleaned:
            return Embedding(vector=[], kind="sparse")

        if self.client:
            try:
                resp = self.client.embeddings.create(model=self.model, input=cleaned)
                vec = resp.data[0].embedding
                return Embedding(vector=vec, kind="dense")
            except Exception as exc:
                logging.error("Embedding failed; falling back to sparse: %s", exc)

        # sparse fallback using token set
        tokens = [t for t in cleaned.lower().split() if t]
        return Embedding(vector=list(tokens), kind="sparse")
