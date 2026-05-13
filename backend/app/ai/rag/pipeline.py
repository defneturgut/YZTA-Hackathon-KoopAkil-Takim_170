"""End-to-end RAG pipeline.

ingest_document → parse → chunk → embed → persist
retrieve(query) → embed → cosine similarity over DocumentChunk rows
generate_grounded_answer → injects top chunks as context → Gemini

Storage uses the relational DB (DocumentChunk.embedding_json) so the
demo runs on plain SQLite. The interfaces match what you'd write
against ChromaDB / pgvector — swap is trivial in production.
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.chunker import chunk_text
from app.ai.rag.parser import extract_text
from app.ai.services.gemini_service import gemini_service
from app.models.document import Document, DocumentChunk

logger = logging.getLogger("aegis.ai.rag.pipeline")


# -------------------------------------------------------------------------
# Internal helpers
# -------------------------------------------------------------------------
def _cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# -------------------------------------------------------------------------
# Retrieval result
# -------------------------------------------------------------------------
@dataclass
class RetrievedChunk:
    document_id: int
    document_title: str
    chunk_index: int
    content: str
    score: float


# -------------------------------------------------------------------------
# Public API
# -------------------------------------------------------------------------
async def ingest_document(
    db: AsyncSession,
    *,
    filename: str,
    file_bytes: bytes,
    title: Optional[str] = None,
    category: str = "genel",
    uploaded_by: Optional[int] = None,
) -> Document:
    """Parse, chunk, embed and persist a knowledge-base document."""
    text, mime = extract_text(filename, file_bytes)
    if not text.strip():
        # Still create a stub so the user sees the upload attempt.
        text = f"(Boş içerik — '{filename}' okunamadı veya metin içermiyor.)"

    chunks = chunk_text(text)
    embeddings = await gemini_service.embed([c.content for c in chunks]) if chunks else []

    doc = Document(
        title=title or filename,
        filename=filename,
        mime_type=mime,
        category=category,
        size_bytes=len(file_bytes),
        chunk_count=len(chunks),
        content_preview=text[:500],
        uploaded_by=uploaded_by,
    )
    db.add(doc)
    await db.flush()

    for chunk, embedding in zip(chunks, embeddings):
        db.add(
            DocumentChunk(
                document_id=doc.id,
                chunk_index=chunk.index,
                content=chunk.content,
                embedding_json=json.dumps(embedding),
                token_count=chunk.token_estimate,
            )
        )

    await db.commit()
    await db.refresh(doc)
    logger.info("Ingested document %s (%d chunks)", doc.title, len(chunks))
    return doc


async def retrieve(
    db: AsyncSession,
    query: str,
    *,
    top_k: int = 4,
    min_score: float = 0.05,
) -> List[RetrievedChunk]:
    """Return the top-k semantically closest chunks to ``query``."""
    query = (query or "").strip()
    if not query:
        return []

    [q_emb] = await gemini_service.embed([query])

    result = await db.execute(
        select(DocumentChunk, Document.title)
        .join(Document, Document.id == DocumentChunk.document_id)
    )
    scored: List[RetrievedChunk] = []
    for chunk, doc_title in result.all():
        try:
            emb = json.loads(chunk.embedding_json)
        except (TypeError, ValueError):
            continue
        score = _cosine(q_emb, emb)
        if score < min_score:
            continue
        scored.append(
            RetrievedChunk(
                document_id=chunk.document_id,
                document_title=doc_title,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=score,
            )
        )
    scored.sort(key=lambda r: r.score, reverse=True)
    return scored[:top_k]


async def generate_grounded_answer(
    db: AsyncSession,
    query: str,
    *,
    system_prompt: str,
    history: Optional[List[dict]] = None,
    top_k: int = 4,
):
    """Retrieve context, call Gemini, return (response, retrieved_chunks)."""
    retrieved = await retrieve(db, query, top_k=top_k)
    context_block = "\n\n".join(
        f"[{i+1}] {r.document_title} (parça #{r.chunk_index}):\n{r.content}"
        for i, r in enumerate(retrieved)
    )
    if context_block:
        grounded_prompt = (
            "Aşağıdaki bilgi tabanı parçalarını kullanarak kullanıcının sorusunu yanıtla. "
            "Sadece bu bilgilere dayan, bilmiyorsan dürüstçe söyle, kaynak numarasını köşeli "
            "parantezle (örn. [1]) belirt.\n\n"
            f"--- BİLGİ TABANI ---\n{context_block}\n--- /BİLGİ TABANI ---\n\n"
            f"Kullanıcı sorusu: {query}"
        )
    else:
        grounded_prompt = (
            "Bilgi tabanında ilgili bir doküman bulunamadı. Yalnızca genel kurumsal "
            "bilgilere dayanarak yanıt ver; emin değilsen 'Bu bilgiye erişemiyorum' de.\n\n"
            f"Kullanıcı sorusu: {query}"
        )

    messages: List[dict] = list(history or [])
    messages.append({"role": "user", "content": grounded_prompt})
    response = await gemini_service.chat(messages, system=system_prompt)
    return response, retrieved
