from __future__ import annotations


def build_prompt(question: str, context: str, citation_mode: bool) -> str:
    cite_rule = (
        "Citations are enabled.\n"
        "Write a clear, human-friendly answer first.\n"
        "Then include exact supporting wording from the context in a collapsible block using this exact format:\n"
        "[[KB_EXACT]]\n"
        "[Source: <doc_name> | page <page_number>]\n"
        "<exact wording copied verbatim from context>\n"
        "[Source: <doc_name> | page <page_number>]\n"
        "<exact wording copied verbatim from context>\n"
        "[[/KB_EXACT]]\n"
        "Rules for the KB_EXACT block:\n"
        "- Use 1 to 3 short verbatim snippets.\n"
        "- Do not invent source names, pages, or wording.\n"
        "- Keep the main answer readable and natural; keep the exact wording only inside KB_EXACT."
        if citation_mode
        else "Citations are disabled. Do not include source lines or any KB_EXACT block."
    )

    return (
        "You are a helpful assistant that answers strictly from provided context. "
        "If context is insufficient, say you do not have enough information.\\n"
        f"{cite_rule}\\n\\n"
        f"Question: {question}\\n\\n"
        f"Context:\\n{context}\\n\\n"
        "Answer:"
    )
