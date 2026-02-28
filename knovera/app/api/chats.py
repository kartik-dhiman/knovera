from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query

from app.core.container import container
from app.generation.llm_client import extractive_fallback
from app.generation.prompt_builder import build_prompt
from app.retrieval.context_builder import build_context
from app.schemas.chat import (
    ChatAskRequest,
    ChatAskResponse,
    ChatCreateRequest,
    ChatDetail,
    ChatIdentityUpdateRequest,
    ChatMessage,
    ChatSettingsUpdateRequest,
    ChatStatusUpdateRequest,
    ChatSummary,
)
from app.schemas.query import Citation

router = APIRouter(prefix="/chats", tags=["chats"])


def _derive_title_from_question(question: str) -> str:
    cleaned = " ".join(question.strip().split())
    if not cleaned:
        return "New chat"
    words = cleaned.split(" ")
    if len(words) <= 2:
        title = cleaned
    else:
        title = " ".join(words[:2])
    return title[:48]


@router.get("", response_model=List[ChatSummary])
def list_chats(include_inactive: bool = Query(False)) -> List[ChatSummary]:
    rows = container.sqlite.list_chats(include_inactive=include_inactive)
    return [ChatSummary(**row) for row in rows]


@router.post("", response_model=ChatSummary)
def create_chat(payload: ChatCreateRequest) -> ChatSummary:
    chat_id = str(uuid4())
    title = payload.title or "New chat"
    kb_id = payload.knowledge_base_id
    user_name = (payload.user_name or "User").strip() or "User"
    assistant_name = (payload.assistant_name or "Assistant").strip() or "Assistant"

    if kb_id:
        kb = container.sqlite.get_knowledge_base(kb_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found")
        valid_ids = []
    else:
        valid_ids = container.sqlite.filter_existing_ready_document_ids(payload.document_ids)

    container.sqlite.create_chat(
        chat_id=chat_id,
        title=title,
        document_ids=valid_ids,
        knowledge_base_id=kb_id,
        user_name=user_name,
        assistant_name=assistant_name,
        citation_mode=True,
        top_k=5,
    )
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=500, detail="Chat was not created")
    return ChatSummary(**row)


@router.get("/{chat_id}", response_model=ChatDetail)
def get_chat(chat_id: str) -> ChatDetail:
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = [ChatMessage(**m) for m in container.sqlite.list_chat_messages(chat_id)]
    return ChatDetail(**row, messages=messages)


@router.post("/{chat_id}/ask", response_model=ChatAskResponse)
def ask_chat(chat_id: str, payload: ChatAskRequest) -> ChatAskResponse:
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    if row.get("status") == "inactive":
        raise HTTPException(status_code=400, detail="Chat is inactive. Reactivate it before querying.")

    kb_id = row.get("knowledge_base_id")
    if kb_id:
        doc_ids = container.sqlite.get_knowledge_base_document_ids(kb_id)
        doc_ids = container.sqlite.filter_existing_ready_document_ids(doc_ids)
    else:
        doc_ids = row.get("document_ids", [])

    if row.get("title") in {"New chat", "New KB Chat"}:
        auto_title = _derive_title_from_question(payload.question)
        container.sqlite.update_chat_title(chat_id, auto_title)

    container.sqlite.add_chat_message(chat_id, role="user", content=payload.question)

    chunks = container.retriever.retrieve(
        query=payload.question,
        top_k=payload.top_k,
        doc_ids=doc_ids if doc_ids else None,
    )

    context = build_context(chunks)
    prompt = build_prompt(payload.question, context, payload.citation_mode)
    answer = container.llm.generate(prompt)

    if not answer:
        answer = extractive_fallback(payload.question, context)

    container.sqlite.add_chat_message(chat_id, role="assistant", content=answer)

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

    messages = [ChatMessage(**m) for m in container.sqlite.list_chat_messages(chat_id)]
    return ChatAskResponse(
        answer=answer,
        citations=[c.model_dump() for c in citations],
        used_chunks=len(chunks),
        chat_id=chat_id,
        messages=messages,
    )


@router.delete("/{chat_id}")
def delete_chat(chat_id: str) -> Dict[str, str]:
    deleted = container.sqlite.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"deleted": chat_id}


@router.patch("/{chat_id}/status", response_model=ChatSummary)
def update_chat_status(chat_id: str, payload: ChatStatusUpdateRequest) -> ChatSummary:
    updated = container.sqlite.update_chat_status(chat_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Chat not found")
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatSummary(**row)


@router.patch("/{chat_id}/identity", response_model=ChatSummary)
def update_chat_identity(chat_id: str, payload: ChatIdentityUpdateRequest) -> ChatSummary:
    ok = container.sqlite.update_chat_identities(
        chat_id=chat_id,
        user_name=payload.user_name.strip(),
        assistant_name=payload.assistant_name.strip(),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatSummary(**row)


@router.patch("/{chat_id}/settings", response_model=ChatSummary)
def update_chat_settings(chat_id: str, payload: ChatSettingsUpdateRequest) -> ChatSummary:
    ok = container.sqlite.update_chat_settings(
        chat_id=chat_id,
        title=payload.title,
        user_name=payload.user_name,
        assistant_name=payload.assistant_name,
        citation_mode=payload.citation_mode,
        top_k=payload.top_k,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Chat not found")
    row = container.sqlite.get_chat(chat_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat not found")
    return ChatSummary(**row)
