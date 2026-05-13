"""Knowledge-base document schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    filename: str
    mime_type: str
    category: str
    size_bytes: int
    chunk_count: int
    content_preview: Optional[str] = None
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentRead
    chunks_indexed: int
    message: str
