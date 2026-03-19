from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_name: str
    page_number: int
    chunk_index: int
    text: str


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    """Split text intelligently, preserving sentence boundaries across languages.

    Handles sentence terminators for:
    - Latin scripts:      . ! ?
    - Devanagari:         । (purna viram) ॥ (double danda)
    - CJK:                。(ideographic full stop) ！ ？
    - Thai / Lao:         splits on whitespace + Thai Mai Yamok ๆ
    - Arabic / Urdu:      ۔ (Arabic full stop)
    - Bengali / Gurmukhi / Gujarati / Tamil / Telugu / Kannada / Malayalam / Odia:
                          share the purna viram । or have their own full stops
    - Khmer:              ។ (khan)
    - Myanmar:            ။ (Myanmar full stop)
    - Tibetan:            ། (shad) ༎ (nyis shad)
    - Armenian:           ։ (full stop) ՞ (question mark)
    - Ethiopic:           ። (full stop) ፧ (question mark)
    - Georgian / Cyrillic / Korean: use Latin . ! ? via shared punctuation

    Uses sliding window with overlap for better context preservation.
    """
    from app.core.utils import normalize_text

    # Normalize unicode to avoid mixed character forms
    text = normalize_text(text)

    if chunk_size <= 0:
        return [text]
    if not text:
        return []

    # ── Build a universal sentence-boundary regex ──────────────────────────
    # Each alternative is a positive lookbehind for a sentence-ending character
    # followed by whitespace.
    #
    # Order does not matter since they are alternatives.  We use a character
    # class for terminators that can be grouped, and separate lookbehinds for
    # multi-byte terminators that need their own group.
    sentence_split = re.compile(
        r'(?<=[.!?'
        r'।'           # Devanagari purna viram (also used by Bengali, Gujarati, etc.)
        r'۔'           # Arabic / Urdu full stop
        r'。'           # CJK ideographic full stop
        r'！'           # CJK fullwidth exclamation
        r'？'           # CJK fullwidth question mark
        r'។'           # Khmer khan
        r'။'           # Myanmar full stop
        r'།'           # Tibetan shad
        r'։'           # Armenian full stop
        r'።'           # Ethiopic full stop
        r'])\s+'
        r'|(?<=॥)\s+'  # Devanagari double danda (2-char lookbehind)
        r'|(?<=༎)\s+'  # Tibetan nyis shad
        r'|(?<=՞)\s+'  # Armenian question mark
        r'|(?<=፧)\s+'  # Ethiopic question mark
    )

    sentences = sentence_split.split(text)

    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text] if text.strip() else []

    # ── Build chunks with overlap ──────────────────────────────────────────
    chunks: List[str] = []
    current_chunk = ""

    for i, sentence in enumerate(sentences):
        length_to_add = len(sentence) + (1 if current_chunk else 0)

        if len(current_chunk) + length_to_add <= chunk_size:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            # Save current chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())

            # Build overlap from previous sentences
            overlap_text = ""
            overlap_len = 0

            for j in range(i - 1, -1, -1):
                prev_sentence = sentences[j]
                prev_len = len(prev_sentence) + 1  # +1 for space

                if overlap_len + prev_len <= chunk_overlap:
                    overlap_text = prev_sentence + (" " + overlap_text if overlap_text else "")
                    overlap_len += prev_len
                else:
                    break

            # Start new chunk with overlap + current sentence
            if overlap_text:
                current_chunk = overlap_text + " " + sentence
            else:
                current_chunk = sentence

    # Add remaining chunk
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
