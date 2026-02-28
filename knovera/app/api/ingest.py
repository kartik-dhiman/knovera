from __future__ import annotations

from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.container import container
from app.schemas.ingest import IngestResponse, IngestResponseItem

router = APIRouter(prefix="/ingest", tags=["ingest"])


def _run_ingest(doc_id: str, file_path: str, file_name: str) -> None:
    try:
        container.ingestion.ingest_pdf(doc_id=doc_id, pdf_path=file_path, doc_name=file_name)
    except Exception as exc:  # noqa: BLE001
        container.sqlite.update_document_status(doc_id, status="failed", error=str(exc))


@router.post("", response_model=IngestResponse)
async def ingest_pdfs(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)) -> IngestResponse:
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded")

    items: List[IngestResponseItem] = []
    upload_root = Path(settings.upload_dir)
    upload_root.mkdir(parents=True, exist_ok=True)

    for uploaded in files:
        if not uploaded.filename or not uploaded.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        doc_id = str(uuid4())
        safe_name = Path(uploaded.filename).name
        out_path = upload_root / f"{doc_id}_{safe_name}"

        data = await uploaded.read()
        out_path.write_bytes(data)

        container.sqlite.create_document(doc_id=doc_id, name=safe_name, path=str(out_path))
        background_tasks.add_task(_run_ingest, doc_id, str(out_path), safe_name)

        items.append(IngestResponseItem(document_id=doc_id, name=safe_name, status="queued"))

    return IngestResponse(items=items)
