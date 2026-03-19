from __future__ import annotations

from dataclasses import dataclass
from typing import List

import fitz


@dataclass
class PageText:
    page_number: int
    text: str


def extract_pdf_pages(pdf_path: str) -> List[PageText]:
    pages: List[PageText] = []
    from app.core.utils import normalize_text

    with fitz.open(pdf_path) as doc:
        for page_idx, page in enumerate(doc):
            raw = page.get_text("text") or ""
            text = normalize_text(raw)
            if text.strip():
                pages.append(PageText(page_number=page_idx + 1, text=text))
    return pages
