"""Chat / AI schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.conversation import MessageRole


class ChatSource(BaseModel):
    """Provenance for a single citation in an AI answer."""

    type: str = Field(description="document | order | shipment | product | tool")
    label: str
    reference: str
    excerpt: Optional[str] = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: Optional[str] = None
    channel: str = "web"


class ChatResponse(BaseModel):
    session_id: str
    message: str
    confidence: float = Field(ge=0, le=1)
    sources: List[ChatSource] = []
    tool_calls: List[Dict[str, Any]] = []
    latency_ms: int
    model: str


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: MessageRole
    content: str
    confidence: Optional[float] = None
    created_at: datetime


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: str
    title: str
    channel: str
    created_at: datetime
    messages: List[MessageRead] = []
