from __future__ import annotations

from typing import List
from typing import Optional

from pydantic import BaseModel, Field


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    document_ids: List[str] = Field(default_factory=list)


class KnowledgeBaseUpdateRequest(BaseModel):
    document_ids: List[str] = Field(default_factory=list)


class KnowledgeBaseEditRequest(BaseModel):
    name: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)


class KnowledgeBaseSummary(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str
    document_ids: List[str]
    document_names: List[str]
    document_count: int
