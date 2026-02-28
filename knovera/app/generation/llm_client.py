from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, prompt: str) -> str:
        # Local-first default path: Ollama chat endpoint.
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            return data.get("message", {}).get("content", "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("LLM call failed, using extractive fallback: %s", exc)
            return ""


def extractive_fallback(question: str, context: str) -> str:
    if not context.strip():
        return "I do not have enough information in the indexed documents to answer that."

    q_words = {w.lower() for w in question.split() if len(w) > 3}
    best_line = ""
    best_score = -1

    for line in context.splitlines():
        if not line.strip() or line.startswith("[Source:"):
            continue
        score = sum(1 for w in q_words if w in line.lower())
        if score > best_score:
            best_score = score
            best_line = line.strip()

    if best_line:
        return best_line
    return "I found related context, but could not form a reliable answer."
