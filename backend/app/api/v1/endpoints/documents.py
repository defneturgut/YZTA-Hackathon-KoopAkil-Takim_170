"""Knowledge-base document endpoints."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.rag.pipeline import ingest_document
from app.database import get_db
from app.models.document import Document, DocumentChunk
from app.schemas.document import DocumentRead, DocumentUploadResponse

router = APIRouter()


@router.get("", response_model=List[DocumentRead])
async def list_documents(db: AsyncSession = Depends(get_db)) -> List[DocumentRead]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return [DocumentRead.model_validate(d) for d in result.scalars().all()]


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    file: UploadFile = File(...),
    title: str | None = Form(default=None),
    category: str = Form(default="genel"),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Dosya adı eksik.")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Dosya boş.")
    doc = await ingest_document(
        db,
        filename=file.filename,
        file_bytes=data,
        title=title,
        category=category,
    )
    return DocumentUploadResponse(
        document=DocumentRead.model_validate(doc),
        chunks_indexed=doc.chunk_count,
        message="Belge başarıyla indekslendi ve bilgi tabanına eklendi.",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(document_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Belge bulunamadı.")
    await db.execute(
        delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
    )
    await db.delete(doc)
    await db.commit()
