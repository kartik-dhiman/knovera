from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.db.vector_store import VectorStore
from app.ingestion.embedder import Embedder


@dataclass
class RetrievedChunk:
    text: str
    score: float
    doc_id: str
    doc_name: str
    page: int
    chunk_index: int


class Retriever:
    def __init__(self, vector_store: VectorStore, embedder: Embedder) -> None:
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve(self, query: str, top_k: Optional[int] = None, doc_ids: Optional[List[str]] = None) -> List[RetrievedChunk]:
        from app.core.utils import normalize_text
        query = normalize_text(query)
        query_vec = self.embedder.embed_query(query)
        where: Optional[Dict[str, Any]] = None
        if doc_ids:
            where = {"doc_id": {"$in": doc_ids}}

        response = self.vector_store.query(
            embedding=query_vec,
            top_k=top_k or settings.retrieval_top_k,
            where=where,
        )

        docs = response.get("documents", [[]])[0]
        metas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        chunks: List[RetrievedChunk] = []
        for text, meta, distance in zip(docs, metas, distances):
            chunks.append(
                RetrievedChunk(
                    text=text,
                    score=1 - float(distance),
                    doc_id=meta.get("doc_id", ""),
                    doc_name=meta.get("doc_name", "unknown"),
                    page=int(meta.get("page", 0)),
                    chunk_index=int(meta.get("chunk_index", 0)),
                )
            )

        return chunks
