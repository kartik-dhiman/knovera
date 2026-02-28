from __future__ import annotations

from typing import List, Optional

from app.core.config import settings
from app.retrieval.retriever import RetrievedChunk


def build_context(chunks: List[RetrievedChunk], max_chars: Optional[int] = None) -> str:
    budget = max_chars or settings.max_context_chars
    used = 0
    parts: List[str] = []

    for c in chunks:
        fragment = f"[Source: {c.doc_name} | page {c.page}]\n{c.text}"
        if used + len(fragment) > budget:
            break
        parts.append(fragment)
        used += len(fragment)

    return "\n\n".join(parts)
