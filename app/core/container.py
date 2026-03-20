from __future__ import annotations

from app.db.sqlite import SQLiteStore
from app.db.vector_store import VectorStore
from app.generation.llm_client import LLMClient
from app.ingestion.embedder import Embedder
from app.ingestion.indexer import IngestionService
from app.retrieval.retriever import Retriever


class Container:
    def __init__(self) -> None:
        self.sqlite = SQLiteStore()
        self.vector = VectorStore()
        self.embedder = Embedder()
        self.ingestion = IngestionService(self.sqlite, self.vector, self.embedder)
        self.retriever = Retriever(self.vector, self.embedder)
        self.llm = LLMClient()


container = Container()
