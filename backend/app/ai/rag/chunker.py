"""Text chunking for the RAG pipeline.

Implements a simple but effective overlapping-window chunker. Documents
are split first on paragraph boundaries to preserve semantic coherence,
then long paragraphs are broken into windows with controlled overlap so
retrieval context never gets clipped mid-sentence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass
class Chunk:
    index: int
    content: str
    token_estimate: int


def _approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def chunk_text(text: str, *, max_chars: int = 1200, overlap: int = 200) -> List[Chunk]:
    """Split text into overlapping chunks suitable for embedding.

    Args:
        text: Raw document text (already extracted from PDF/DOCX/etc).
        max_chars: Soft upper bound per chunk (characters, not tokens).
        overlap: Overlap window in characters between consecutive chunks.
    """
    text = (text or "").strip()
    if not text:
        return []

    # Step 1 — paragraph-level split.
    paragraphs: List[str] = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    # Step 2 — pack paragraphs into chunks ≤ max_chars.
    raw_chunks: List[str] = []
    buffer = ""
    for para in paragraphs:
        if len(buffer) + len(para) + 2 <= max_chars:
            buffer = (buffer + "\n\n" + para).strip() if buffer else para
        else:
            if buffer:
                raw_chunks.append(buffer)
            if len(para) <= max_chars:
                buffer = para
            else:
                # Step 3 — split oversized paragraphs with overlap.
                start = 0
                while start < len(para):
                    end = min(start + max_chars, len(para))
                    raw_chunks.append(para[start:end])
                    if end == len(para):
                        break
                    start = end - overlap
                buffer = ""
    if buffer:
        raw_chunks.append(buffer)

    return [
        Chunk(index=i, content=c, token_estimate=_approx_tokens(c))
        for i, c in enumerate(raw_chunks)
    ]
