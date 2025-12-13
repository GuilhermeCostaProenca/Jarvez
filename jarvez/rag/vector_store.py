from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple

from jarvez.rag.embedder import Embedding


@dataclass
class VectorDocument:
    doc_id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Embedding


class VectorStore:
    """Simple JSON-backed vector store with dense/sparse support."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.docs: Dict[str, VectorDocument] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8-sig"))
            for item in data:
                emb = Embedding(vector=item["embedding"]["vector"], kind=item["embedding"]["kind"])
                self.docs[item["doc_id"]] = VectorDocument(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    metadata=item.get("metadata", {}),
                    embedding=emb,
                )
        except Exception:
            self.docs = {}

    def _save(self) -> None:
        payload = [
            {
                "doc_id": doc.doc_id,
                "text": doc.text,
                "metadata": doc.metadata,
                "embedding": {"vector": doc.embedding.vector, "kind": doc.embedding.kind},
            }
            for doc in self.docs.values()
        ]
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add(self, document: VectorDocument) -> None:
        self.docs[document.doc_id] = document
        self._save()

    def add_bulk(self, documents: List[VectorDocument]) -> None:
        for doc in documents:
            self.docs[doc.doc_id] = doc
        self._save()

    def query(self, query_embedding: Embedding, top_k: int = 3) -> List[Tuple[VectorDocument, float]]:
        results: List[Tuple[VectorDocument, float]] = []
        for doc in self.docs.values():
            score = self._similarity(query_embedding, doc.embedding)
            results.append((doc, score))
        results.sort(key=lambda pair: pair[1], reverse=True)
        return results[:top_k]

    def _similarity(self, a: Embedding, b: Embedding) -> float:
        if a.kind == "dense" and b.kind == "dense":
            return self._cosine(a.vector, b.vector)
        # sparse fallback: jaccard
        set_a = set(a.vector)
        set_b = set(b.vector)
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    @staticmethod
    def _cosine(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        if len(vec_a) != len(vec_b):
            # length mismatch fallback
            size = min(len(vec_a), len(vec_b))
            vec_a = vec_a[:size]
            vec_b = vec_b[:size]
        dot = sum(x * y for x, y in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(x * x for x in vec_a))
        norm_b = math.sqrt(sum(y * y for y in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
