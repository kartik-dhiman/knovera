from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, WebSocket

import asyncio

import logging

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

logger = logging.getLogger(__name__)


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
    # original HTTP handler preserved for backwards compatibility
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


@router.websocket("/ws/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: str):
    """WebSocket endpoint to handle chat questions and replies.

    Client should send JSON messages containing ``question``,
    ``citation_mode`` and ``top_k``.  The server replies with streamed tokens
    followed by a complete response with citations.
    """
    await websocket.accept()

    async def fetch_chunks(question: str, top_k: int, doc_ids: list):
        # run blocking retrieval in thread pool
        return await asyncio.get_running_loop().run_in_executor(
            None, container.retriever.retrieve, question, top_k, doc_ids
        )

    async def build_prompt_async(question: str, context: str, citation_mode: bool) -> str:
        return await asyncio.get_running_loop().run_in_executor(
            None, build_prompt, question, context, citation_mode
        )

    async def stream_llm_tokens(prompt: str):
        """Run the blocking requests-based LLM stream in a thread pool so the
        asyncio event loop is never blocked between tokens.
        Yields tokens as they arrive from Ollama.
        """
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _produce() -> None:
            try:
                for token in container.llm.generate_stream(prompt):
                    loop.call_soon_threadsafe(queue.put_nowait, token)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)  # sentinel

        # Fire producer in thread — do NOT await so it runs concurrently
        producer = loop.run_in_executor(None, _produce)

        while True:
            token = await queue.get()
            if token is None:
                break
            yield token

        await producer  # ensure thread cleanup / surface any exception

    try:
        while True:
            msg = await websocket.receive_json()
            question = msg.get("question", "").strip()
            citation_mode = msg.get("citation_mode", True)
            top_k = msg.get("top_k", 5)

            logger.info("WS chat %s received question '%s' (citation_mode=%s, top_k=%s)", chat_id, question, citation_mode, top_k)

            row = container.sqlite.get_chat(chat_id)
            if not row:
                await websocket.send_json({"error": "Chat not found"})
                continue
            if row.get("status") == "inactive":
                await websocket.send_json({"error": "Chat is inactive"})
                continue

            if row.get("title") in {"New chat", "New KB Chat"}:
                auto_title = _derive_title_from_question(question)
                container.sqlite.update_chat_title(chat_id, auto_title)

            container.sqlite.add_chat_message(chat_id, role="user", content=question)

            if row.get("knowledge_base_id"):
                doc_ids = container.sqlite.get_knowledge_base_document_ids(row["knowledge_base_id"])
                doc_ids = container.sqlite.filter_existing_ready_document_ids(doc_ids)
            else:
                doc_ids = row.get("document_ids", [])

            # let client know we're gathering context
            await websocket.send_json({"type":"info","message":"retrieving context"})
            chunks = await fetch_chunks(question, top_k, doc_ids if doc_ids else None)
            logger.info("Retrieved %d chunks", len(chunks))

            context = build_context(chunks)
            prompt = await build_prompt_async(question, context, citation_mode)
            logger.info("Built prompt of length %d", len(prompt))
            
            # Tell client LLM is generating (shows immediately, before first token)
            await websocket.send_json({"type": "info", "message": "generating answer"})

            # Stream tokens — runs in a thread pool to keep event loop free
            answer = ""
            logger.info("Starting token stream from LLM")
            async for token in stream_llm_tokens(prompt):
                answer += token
                await websocket.send_json({"type": "token", "content": token})
            
            if not answer:
                answer = extractive_fallback(question, context)
                await websocket.send_json({"type": "token", "content": answer})

            container.sqlite.add_chat_message(chat_id, role="assistant", content=answer)

            citations: List[Citation] = []
            if citation_mode:
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
            # Send complete response with citations at the end
            await websocket.send_json({
                "type": "complete",
                "answer": answer,
                "citations": [c.model_dump() for c in citations],
                "used_chunks": len(chunks),
                "chat_id": chat_id,
                "messages": [m.model_dump() for m in messages],
            })
    except Exception as exc:
        # websocket disconnects cleanly or network error
        logger.error("WebSocket handler exception for chat %s: %s", chat_id, exc, exc_info=True)
        # stop handling this connection
        return


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
