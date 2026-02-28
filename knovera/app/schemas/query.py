from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    citation_mode: bool = True
    top_k: int = 5
    document_ids: Optional[List[str]] = None


class Citation(BaseModel):
    doc_id: str
    doc_name: str
    page: int
    chunk_index: int
    score: float


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation]
    used_chunks: int
