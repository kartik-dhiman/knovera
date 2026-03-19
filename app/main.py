from __future__ import annotations

from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.chats import router as chats_router
from app.api.documents import router as documents_router
from app.api.ingest import router as ingest_router
from app.api.knowledge_bases import router as knowledge_bases_router
from app.api.query import router as query_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.utils import ensure_data_dirs
from app.web.routes import router as web_router

setup_logging()
ensure_data_dirs()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

app.include_router(web_router)
app.include_router(ingest_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(chats_router, prefix="/api")
app.include_router(knowledge_bases_router, prefix="/api")


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}
