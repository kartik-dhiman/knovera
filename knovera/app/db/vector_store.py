from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

# Hard-disable Chroma telemetry before client initialization.
os.environ.setdefault("ANONYMIZED_TELEMETRY", "FALSE")

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings

from app.core.config import settings


class VectorStore:
    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path=settings.chroma_dir,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection: Collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        self.collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    def query(self, embedding: List[float], top_k: int, where: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return self.collection.query(query_embeddings=[embedding], n_results=top_k, where=where)

    def delete_document_chunks(self, doc_id: str) -> None:
        self.collection.delete(where={"doc_id": doc_id})
