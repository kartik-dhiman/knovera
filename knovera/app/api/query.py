from __future__ import annotations

from typing import List

from fastapi import APIRouter

from app.core.container import container
from app.generation.llm_client import extractive_fallback
from app.generation.prompt_builder import build_prompt
from app.retrieval.context_builder import build_context
from app.schemas.query import Citation, QueryRequest, QueryResponse

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
def query_docs(payload: QueryRequest) -> QueryResponse:
    chunks = container.retriever.retrieve(
        query=payload.question,
        top_k=payload.top_k,
        doc_ids=payload.document_ids,
    )

    context = build_context(chunks)
    prompt = build_prompt(payload.question, context, payload.citation_mode)
    answer = container.llm.generate(prompt)

    if not answer:
        answer = extractive_fallback(payload.question, context)

    citations: List[Citation] = []
    if payload.citation_mode:
        citations = [
            Citation(
                doc_id=c.doc_id,
                doc_name=c.doc_name,
                page=c.page,
                chunk_index=c.chunk_index,
                score=round(c.score, 3),
            )
            for c in chunks
        ]

    return QueryResponse(answer=answer, citations=citations, used_chunks=len(chunks))
