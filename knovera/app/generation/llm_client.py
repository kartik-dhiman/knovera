from __future__ import annotations

import json
import logging
from typing import Any, Dict

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(self) -> None:
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def generate(self, prompt: str, _retry: bool = False) -> str:
        """Generate text from the LLM.

        If the request fails with an HTTP 500 (often due to an oversized prompt),
        retry once with a truncated version of the prompt.  The ``_retry`` flag
        prevents infinite recursion.
        """
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
        except requests.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else 'unknown'
            body = http_err.response.text if http_err.response is not None else '<no body>'
            logger.warning(
                "LLM HTTP error status=%s url=%s payload_len=%d response=%s",
                status,
                self.base_url,
                len(payload.get('messages', [{}])[0].get('content', '')),
                body,
            )
            # if it was a 500 and we haven't retried yet, try with shortened prompt
            if status == 500 and not _retry:
                short = prompt[:4000]
                logger.warning("Retrying LLM call with truncated prompt (original %d chars)", len(prompt))
                return self.generate(short, _retry=True)
            return ""
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM call failed (url=%s payload_len=%d) : %s / %s",
                self.base_url,
                len(prompt),
                type(exc).__name__,
                exc,
            )
            # if not already retried attempt with truncation
            if not _retry and len(prompt) > 4000:
                short = prompt[:4000]
                logger.warning("Retrying LLM call after exception with truncated prompt")
                return self.generate(short, _retry=True)
            return ""

    def generate_stream(self, prompt: str, _retry: bool = False):
        """Stream tokens from the LLM as they arrive.
        
        Yields individual tokens from Ollama's streaming response.
        Falls back to non-streaming retry with truncation on HTTP 500.
        """
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True,
        }

        try:
            logger.info("LLM streaming request payload length %d", len(prompt))
            resp = requests.post(f"{self.base_url}/api/chat", json=payload, timeout=60, stream=True)
            resp.raise_for_status()
            logger.info("LLM streaming response status %s", resp.status_code)
            
            for line in resp.iter_lines():
                logger.debug("LLM stream line raw: %r", line)
                if not line:
                    continue
                try:
                    chunk = line.decode() if isinstance(line, bytes) else line
                    data = json.loads(chunk)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        logger.debug("LLM yielded token: %s", token)
                        yield token
                except (ValueError, KeyError) as e:
                    logger.debug("Skipping malformed LLM stream line: %s", e)
                    # skip malformed lines
                    pass
                    
        except requests.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else 'unknown'
            logger.warning(
                "LLM streaming HTTP error status=%s url=%s payload_len=%d",
                status,
                self.base_url,
                len(prompt),
            )
            # if it was a 500 and we haven't retried, fall back to non-streaming with truncation
            if status == 500 and not _retry:
                short = prompt[:4000]
                logger.warning("Retrying LLM stream with truncated prompt (original %d chars)", len(prompt))
                yield from self.generate_stream(short, _retry=True)
            else:
                return
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LLM streaming failed (url=%s payload_len=%d) : %s / %s",
                self.base_url,
                len(prompt),
                type(exc).__name__,
                exc,
            )
            if not _retry and len(prompt) > 4000:
                short = prompt[:4000]
                logger.warning("Retrying LLM stream after exception with truncated prompt")
                yield from self.generate_stream(short, _retry=True)
            else:
                return


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
