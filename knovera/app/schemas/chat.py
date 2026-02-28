from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatCreateRequest(BaseModel):
    title: Optional[str] = None
    document_ids: List[str] = Field(default_factory=list)
    knowledge_base_id: Optional[str] = None
    user_name: Optional[str] = None
    assistant_name: Optional[str] = None


class ChatAskRequest(BaseModel):
    question: str = Field(min_length=1)
    citation_mode: bool = True
    top_k: int = 5


class ChatStatusUpdateRequest(BaseModel):
    status: str = Field(pattern="^(active|inactive)$")


class ChatIdentityUpdateRequest(BaseModel):
    user_name: str = Field(min_length=1)
    assistant_name: str = Field(min_length=1)


class ChatSettingsUpdateRequest(BaseModel):
    title: Optional[str] = None
    user_name: Optional[str] = None
    assistant_name: Optional[str] = None
    citation_mode: Optional[bool] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class ChatMessage(BaseModel):
    role: str
    content: str
    created_at: str


class ChatSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    document_ids: List[str]
    document_names: List[str]
    knowledge_base_id: Optional[str] = None
    knowledge_base_name: Optional[str] = None
    user_name: str = "User"
    assistant_name: str = "Assistant"
    citation_mode: bool = True
    top_k: int = 5
    status: str = "active"


class ChatDetail(ChatSummary):
    messages: List[ChatMessage]


class ChatAskResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]]
    used_chunks: int
    chat_id: str
    messages: List[ChatMessage]
