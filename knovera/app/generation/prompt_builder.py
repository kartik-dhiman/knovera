from __future__ import annotations


def is_hindi_text(text: str) -> bool:
    """Check if text contains Hindi characters (Devanagari script)."""
    return any('\u0900' <= c <= '\u097F' for c in text)


def build_prompt(question: str, context: str, citation_mode: bool) -> str:
    """Build a strictly extractive RAG prompt.

    The LLM is forbidden from using its pre-trained knowledge.
    Every claim in the answer must come verbatim or paraphrased directly
    from the provided context passages. Devanagari script is always preserved.
    """
    from app.core.utils import normalize_text

    question = normalize_text(question)
    context = normalize_text(context)

    is_hindi = is_hindi_text(question) or is_hindi_text(context)

    # ── Core identity & strict grounding rules ──────────────────────────────
    system_msg = """\
You are a document reader. Your ONLY job is to extract and present information \
that exists in the Context below. You must follow these rules without exception:

STRICT RULES:
1. Use ONLY information from the Context. Do not use any pre-trained knowledge, \
general facts, or assumptions from outside the Context.
2. If the answer is not found in the Context, respond with exactly: \
"I could not find an answer in the provided documents."
3. Do not infer, guess, or add information that is not explicitly stated in the Context.
4. Answer in the same language as the Question.
5. Structure your answer clearly using bullet points or numbered steps where appropriate.
6. Be concise — do not pad the answer with unnecessary words.\
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
- Copy the text character-for-character from the Context — preserve Hindi/Devanagari script exactly, never transliterate.
- Do not invent source names, page numbers, or any text not in the Context.
- IMPORTANT: [[KB_EXACT]] and [[/KB_EXACT]] must ALWAYS appear as a matched pair. Never write one without the other.
- If you have no relevant excerpt to cite, omit the [[KB_EXACT]] block entirely — do not write an empty block."""
    else:
        cite_rule = "\nDo not include any source citations or KB_EXACT blocks."

    # ── Hindi-specific guard ─────────────────────────────────────────────────
    hindi_note = (
        "\nSCRIPT NOTE: The Context contains Devanagari (Hindi) text. "
        "When copying text into the evidence block, reproduce it in its original "
        "Devanagari characters — never romanise or transliterate."
        if is_hindi else ""
    )

    return (
        f"{system_msg}"
        f"{cite_rule}"
        f"{hindi_note}\n\n"
        f"Question: {question}\n\n"
        f"Context:\n{context}\n\n"
        "Answer:"
    )
