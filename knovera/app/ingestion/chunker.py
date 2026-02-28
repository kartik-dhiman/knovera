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
    """Split text intelligently, preserving sentence boundaries for both English and Hindi.
    
    Uses sliding window with overlap for better context preservation.
    For Hindi text, uses Devanagari sentence terminators (।, ।।) in addition to English punctuation.
    """
    from app.core.utils import normalize_text

    # normalize unicode to avoid mixed character forms
    text = normalize_text(text)

    if chunk_size <= 0:
        return [text]
    if not text:
        return []

    # Split on sentence boundaries
    # Matches: English punctuation (. ! ?) or Hindi punctuation (। ।।)
    # Preserves the punctuation in the split
    sentences = re.split(r'(?<=[।।.!?])\s+', text)
    
    # Filter out empty sentences
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return [text] if text.strip() else []
    
    # Build chunks with overlap
    chunks: List[str] = []
    current_chunk = ""
    
    for i, sentence in enumerate(sentences):
        # Calculate length including space if not first in chunk
        length_to_add = len(sentence) + (1 if current_chunk else 0)
        
        if len(current_chunk) + length_to_add <= chunk_size:
            # Sentence fits in current chunk
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            # Current chunk is full, save it
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap: include previous sentences for context
            overlap_text = ""
            overlap_len = 0
            
            # Walk backwards to include overlap from previous sentences
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
