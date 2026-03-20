from __future__ import annotations

import re

# Keywords that signal a broad / overview question (case-insensitive)
_BROAD_PATTERNS = re.compile(
    r'\b(summar|overview|explain\s+all|describe\s+all|list\s+all'
    r'|tell\s+me\s+(everything|about)|give\s+me|share|show\s+me'
    r'|what\s+(is|are)\s+(the|all|every)|key\s+(points?|ideas?|themes?)'
    r'|main\s+(points?|ideas?|themes?)|full|complete|entire|whole)\b',
    re.IGNORECASE,
)


def is_broad_question(question: str) -> bool:
    """Return True if the question asks for a summary / overview / broad listing."""
    return bool(_BROAD_PATTERNS.search(question))


def build_prompt(question: str, context: str, citation_mode: bool) -> str:
    """Build a strictly extractive RAG prompt with multilingual support.

    The LLM is forbidden from using its pre-trained knowledge.
    Every claim in the answer must come verbatim or paraphrased directly
    from the provided context passages. All non-Latin scripts are preserved
    exactly as they appear in the source documents.
    """
    from app.core.utils import normalize_text, script_preservation_note

    question = normalize_text(question)
    context = normalize_text(context)

    broad = is_broad_question(question)

    # ── Core identity & strict grounding rules ──────────────────────────────
    system_msg = """\
You are a document reader. Your job is to understand what the user is asking for \
and fulfil their request using ONLY the information in the Context below.

STRICT RULES:
1. Use ONLY information from the Context. Do not use any pre-trained knowledge, \
general facts, or assumptions from outside the Context.
2. Understand the user's INTENT, not just their literal words. For example, \
"share verse" means "show me a verse", "explain the summary" means "present the \
summary that appears in the documents", "give me summary" means "summarise all \
the content in the Context", etc.
3. If the Context truly contains nothing relevant to the user's request, respond \
with exactly: "I could not find an answer in the provided documents."
4. Do not fabricate or add information that does not exist in the Context.
5. Answer in the same language as the Question.
6. The Context may contain text in any language or script (Hindi, Arabic, Chinese, \
Korean, Japanese, Thai, Russian, Tamil, etc.). Treat all scripts equally.\
"""

    # ── Depth guidance: concise vs. thorough ─────────────────────────────────
    if broad:
        depth_note = """
RESPONSE DEPTH:
The user is asking for a broad overview or summary. Cover ALL the key points \
from every part of the Context. Use bullet points or numbered items. \
Include specific details, names, numbers, and verses/text references that appear \
in the Context. Do not be brief — be thorough and comprehensive.\
"""
    else:
        depth_note = """
RESPONSE DEPTH:
Be concise — answer the specific question directly without unnecessary padding.\
"""

    # ── Citation format ──────────────────────────────────────────────────────
    if citation_mode:
        cite_rule = """
CITATION FORMAT (required):
After your answer, add an evidence block using EXACTLY this format:

[[KB_EXACT]]
[Source: <document_name> | page <number>]
<copy the exact sentence(s) from the Context that support your answer>
[[/KB_EXACT]]

Rules for the evidence block:
- Include 1 to 3 short verbatim excerpts that directly back up your answer.
- Copy the text character-for-character from the Context — preserve the original \
script exactly (Devanagari, Arabic, CJK, Cyrillic, etc.). Never romanise or transliterate.
- Do not invent source names, page numbers, or any text not in the Context.
- IMPORTANT: [[KB_EXACT]] and [[/KB_EXACT]] must ALWAYS appear as a matched pair. \
Never write one without the other.
- If you have no relevant excerpt to cite, omit the [[KB_EXACT]] block entirely — \
do not write an empty block."""
    else:
        cite_rule = "\nDo not include any source citations or KB_EXACT blocks."

    # ── Auto-detected script-preservation note ───────────────────────────────
    script_note = script_preservation_note(context) or script_preservation_note(question)

    return (
        f"{system_msg}"
        f"{depth_note}"
        f"{cite_rule}"
        f"{script_note}\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )
