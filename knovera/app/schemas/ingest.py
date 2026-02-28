from __future__ import annotations

from typing import List

from pydantic import BaseModel


class IngestResponseItem(BaseModel):
    document_id: str
    name: str
    status: str


class IngestResponse(BaseModel):
    items: List[IngestResponseItem]
