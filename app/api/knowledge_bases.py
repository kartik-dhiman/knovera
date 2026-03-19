from __future__ import annotations

from typing import List
from uuid import uuid4

from fastapi import APIRouter, HTTPException

from app.core.container import container
from app.schemas.knowledge_base import (
    KnowledgeBaseCreateRequest,
    KnowledgeBaseEditRequest,
    KnowledgeBaseSummary,
    KnowledgeBaseUpdateRequest,
)

router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.get("", response_model=List[KnowledgeBaseSummary])
def list_knowledge_bases() -> List[KnowledgeBaseSummary]:
    rows = container.sqlite.list_knowledge_bases()
    return [KnowledgeBaseSummary(**row) for row in rows]


@router.post("", response_model=KnowledgeBaseSummary)
def create_knowledge_base(payload: KnowledgeBaseCreateRequest) -> KnowledgeBaseSummary:
    valid_doc_ids = container.sqlite.filter_existing_ready_document_ids(payload.document_ids)
    kb_id = str(uuid4())
    container.sqlite.create_knowledge_base(kb_id=kb_id, name=payload.name.strip(), document_ids=valid_doc_ids)
    kb = container.sqlite.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=500, detail="Knowledge base creation failed")
    return KnowledgeBaseSummary(**kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseSummary)
def get_knowledge_base(kb_id: str) -> KnowledgeBaseSummary:
    kb = container.sqlite.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return KnowledgeBaseSummary(**kb)


@router.post("/{kb_id}/documents", response_model=KnowledgeBaseSummary)
def add_documents_to_knowledge_base(kb_id: str, payload: KnowledgeBaseUpdateRequest) -> KnowledgeBaseSummary:
    kb = container.sqlite.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    valid_doc_ids = container.sqlite.filter_existing_ready_document_ids(payload.document_ids)
    container.sqlite.add_documents_to_knowledge_base(kb_id=kb_id, document_ids=valid_doc_ids)
    updated = container.sqlite.get_knowledge_base(kb_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Knowledge base update failed")
    return KnowledgeBaseSummary(**updated)


@router.patch("/{kb_id}", response_model=KnowledgeBaseSummary)
def edit_knowledge_base(kb_id: str, payload: KnowledgeBaseEditRequest) -> KnowledgeBaseSummary:
    kb = container.sqlite.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")

    valid_doc_ids = container.sqlite.filter_existing_ready_document_ids(payload.document_ids)
    ok = container.sqlite.update_knowledge_base(kb_id=kb_id, name=payload.name, document_ids=valid_doc_ids)
    if not ok:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    updated = container.sqlite.get_knowledge_base(kb_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Knowledge base update failed")
    return KnowledgeBaseSummary(**updated)

@router.delete("/{kb_id}")
def delete_knowledge_base(kb_id: str) -> dict:
    """Delete a knowledge base and all its document associations."""
    kb = container.sqlite.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    deleted = container.sqlite.delete_knowledge_base(kb_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete knowledge base")
    
    return {"deleted": kb_id, "name": kb.get("name", "")}