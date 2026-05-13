"""Shipments + their tracking logs (event history)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShipmentStatus(str, enum.Enum):
    CREATED = "created"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    AT_HUB = "at_hub"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    EXCEPTION = "exception"


class Shipment(Base):
    __tablename__ = "shipments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tracking_code: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.id"), index=True, nullable=True
    )

    carrier: Mapped[str] = mapped_column(String(64), default="Yurtiçi Kargo", nullable=False)
    origin_city: Mapped[str] = mapped_column(String(128), default="İstanbul", nullable=False)
    destination_city: Mapped[str] = mapped_column(String(128), nullable=False)
    current_location: Mapped[str] = mapped_column(String(255), default="Depo", nullable=False)

    status: Mapped[ShipmentStatus] = mapped_column(
        SAEnum(ShipmentStatus, native_enum=False, length=24),
        default=ShipmentStatus.CREATED,
        nullable=False,
        index=True,
    )

    risk_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ai_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    estimated_delivery: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    delivered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    order: Mapped[Optional["Order"]] = relationship(back_populates="shipments")  # type: ignore[name-defined]
    logs: Mapped[List["ShipmentLog"]] = relationship(
        back_populates="shipment",
        cascade="all, delete-orphan",
        order_by="ShipmentLog.created_at",
    )

    @property
    def hours_since_update(self) -> float:
        """How many hours since the last status change. Used by anomaly detection."""
        if not self.updated_at:
            return 0.0
        now = datetime.now(self.updated_at.tzinfo) if self.updated_at.tzinfo else datetime.utcnow()
        return (now - self.updated_at).total_seconds() / 3600.0


class ShipmentLog(Base):
    __tablename__ = "shipment_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), index=True, nullable=False
    )
    event: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    shipment: Mapped[Shipment] = relationship(back_populates="logs")
