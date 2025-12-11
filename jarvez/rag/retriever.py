from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from jarvez.rag.embedder import Embedder, Embedding
from jarvez.rag.vector_store import VectorDocument, VectorStore


@dataclass
class RetrievedChunk:
    text: str
    metadata: Dict[str, Any]
    score: float


class Retriever:
    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self.embedder = embedder
        self.store = store

    def index_document(self, doc_id: str, text: str, metadata: Dict[str, Any]) -> None:
        embedding = self.embedder.embed(text)
        document = VectorDocument(doc_id=doc_id, text=text, metadata=metadata, embedding=embedding)
        self.store.add(document)

    def index_bulk(self, items: List[Dict[str, Any]]) -> None:
        docs = []
        for item in items:
            embedding = self.embedder.embed(item["text"])
            docs.append(
                VectorDocument(
                    doc_id=item["doc_id"],
                    text=item["text"],
                    metadata=item.get("metadata", {}),
                    embedding=embedding,
                )
            )
        if docs:
            self.store.add_bulk(docs)

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedChunk]:
        query_embedding = self.embedder.embed(query)
        matches = self.store.query(query_embedding, top_k=top_k)
        chunks: List[RetrievedChunk] = []
        for doc, score in matches:
            if score <= 0:
                continue
            chunks.append(RetrievedChunk(text=doc.text, metadata=doc.metadata, score=score))
        return chunks
