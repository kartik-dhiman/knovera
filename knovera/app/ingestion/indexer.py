from __future__ import annotations

import logging
from pathlib import Path
from typing import List
from uuid import uuid4

from app.core.config import settings
from app.db.sqlite import SQLiteStore
from app.db.vector_store import VectorStore
from app.ingestion.chunker import Chunk, chunk_text
from app.ingestion.embedder import Embedder
from app.ingestion.pdf_parser import extract_pdf_pages

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, sqlite_store: SQLiteStore, vector_store: VectorStore, embedder: Embedder) -> None:
        self.sqlite_store = sqlite_store
        self.vector_store = vector_store
        self.embedder = embedder

    def ingest_pdf(self, doc_id: str, pdf_path: str, doc_name: str) -> int:
        try:
            logger.info("Ingesting %s", doc_name)
            self.sqlite_store.update_document_status(doc_id, "processing")

            pages = extract_pdf_pages(pdf_path)
            logger.debug("Extracted %d pages from %s", len(pages), doc_name)
            
            chunks: List[Chunk] = []

            for page in pages:
                page_chunks = chunk_text(
                    text=page.text,
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap,
                )
                for idx, text_piece in enumerate(page_chunks):
                    chunks.append(
                        Chunk(
                            chunk_id=str(uuid4()),
                            doc_id=doc_id,
                            doc_name=doc_name,
                            page_number=page.page_number,
                            chunk_index=idx,
                            text=text_piece,
                        )
                    )

            if not chunks:
                raise ValueError("No extractable text found in PDF")

            logger.debug("Created %d chunks", len(chunks))
            
            texts = [c.text for c in chunks]
            logger.debug("Embedding %d texts", len(texts))
            embeddings = self.embedder.embed_texts(texts)

            ids = [c.chunk_id for c in chunks]
            metadatas = [
                {
                    "doc_id": c.doc_id,
                    "doc_name": c.doc_name,
                    "page": c.page_number,
                    "chunk_index": c.chunk_index,
                    "source": Path(pdf_path).name,
                }
                for c in chunks
            ]

            logger.debug("Upserting %d chunks to vector store", len(ids))
            self.vector_store.upsert_chunks(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
            self.sqlite_store.update_document_status(doc_id, "ready", chunk_count=len(chunks))
            logger.info("Successfully ingested %d chunks for %s", len(chunks), doc_name)
            return len(chunks)
        except Exception as exc:  # noqa: BLE001
            logger.error("Ingestion failed for %s: %s", doc_name, exc, exc_info=True)
            raise
