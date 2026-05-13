"""Shipment schemas + AI risk analysis output."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.shipment import ShipmentStatus


class ShipmentCreate(BaseModel):
    tracking_code: Optional[str] = None  # auto-generated if missing
    order_id: Optional[int] = None
    carrier: str = "Yurtiçi Kargo"
    origin_city: str = "İstanbul"
    destination_city: str = Field(min_length=1)
    estimated_delivery: Optional[datetime] = None


class ShipmentLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event: str
    location: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime


class ShipmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracking_code: str
    order_id: Optional[int] = None
    carrier: str
    origin_city: str
    destination_city: str
    current_location: str
    status: ShipmentStatus
    risk_score: float
    ai_summary: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    logs: List[ShipmentLogRead] = []


class ShipmentAIAnalysis(BaseModel):
    """Structured output produced by the logistics AI."""

    tracking_code: str
    risk_level: str = Field(description="low | medium | high | critical")
    risk_score: float = Field(ge=0, le=1)
    reason: str
    recommended_action: str
    confidence_score: float = Field(ge=0, le=1)
