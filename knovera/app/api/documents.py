from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.container import container

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents() -> dict:
    return {"items": container.sqlite.list_documents()}


@router.delete("/{doc_id}")
def delete_document(doc_id: str) -> dict:
    doc = container.sqlite.delete_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    container.vector.delete_document_chunks(doc_id)

    path = Path(doc["path"])
    if path.exists():
        path.unlink()

    return {"deleted": doc_id}
