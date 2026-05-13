"""Alert schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertSeverity


class AlertCreate(BaseModel):
    title: str
    message: str
    category: str = "general"
    severity: AlertSeverity = AlertSeverity.INFO
    source: str = "system"
    related_entity: Optional[str] = None


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    category: str
    severity: AlertSeverity
    is_read: bool
    is_resolved: bool
    source: str
    related_entity: Optional[str] = None
    created_at: datetime
