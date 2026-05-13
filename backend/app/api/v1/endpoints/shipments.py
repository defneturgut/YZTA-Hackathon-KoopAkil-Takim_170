"""Shipment endpoints with AI anomaly detection."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.prompts import load_prompt
from app.ai.services.gemini_service import gemini_service
from app.database import get_db
from app.models.alert import Alert, AlertSeverity
from app.models.shipment import Shipment, ShipmentLog, ShipmentStatus
from app.schemas.shipment import (
    ShipmentAIAnalysis,
    ShipmentCreate,
    ShipmentRead,
)

logger = logging.getLogger("aegis.api.shipments")
router = APIRouter()


@router.get("", response_model=List[ShipmentRead])
async def list_shipments(
    status_filter: ShipmentStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> List[ShipmentRead]:
    stmt = (
        select(Shipment)
        .options(selectinload(Shipment.logs))
        .order_by(Shipment.created_at.desc())
    )
    if status_filter:
        stmt = stmt.where(Shipment.status == status_filter)
    result = await db.execute(stmt)
    return [ShipmentRead.model_validate(s) for s in result.scalars().all()]


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def get_shipment(
    shipment_id: int, db: AsyncSession = Depends(get_db)
) -> ShipmentRead:
    stmt = (
        select(Shipment)
        .options(selectinload(Shipment.logs))
        .where(Shipment.id == shipment_id)
    )
    result = await db.execute(stmt)
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı.")
    return ShipmentRead.model_validate(shipment)


@router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    payload: ShipmentCreate, db: AsyncSession = Depends(get_db)
) -> ShipmentRead:
    tracking_code = payload.tracking_code or _new_tracking_code()
    shipment = Shipment(
        tracking_code=tracking_code,
        order_id=payload.order_id,
        carrier=payload.carrier,
        origin_city=payload.origin_city,
        destination_city=payload.destination_city,
        estimated_delivery=payload.estimated_delivery,
    )
    db.add(shipment)
    await db.flush()
    db.add(
        ShipmentLog(
            shipment_id=shipment.id,
            event="Kargo oluşturuldu",
            location=shipment.origin_city,
        )
    )
    await db.commit()
    await db.refresh(shipment)
    # eager-load logs for response
    await db.refresh(shipment, ["logs"])
    return ShipmentRead.model_validate(shipment)


@router.post("/{shipment_id}/check-status", response_model=ShipmentAIAnalysis)
async def check_status(
    shipment_id: int, db: AsyncSession = Depends(get_db)
) -> ShipmentAIAnalysis:
    """Run AI anomaly analysis and update the shipment row."""
    shipment = await db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı.")

    # Build the prompt for structured output.
    hours = shipment.hours_since_update
    prompt = (
        f"Kargo: {shipment.tracking_code}\n"
        f"Durum: {shipment.status.value}\n"
        f"Konum: {shipment.current_location}\n"
        f"Hedef: {shipment.destination_city}\n"
        f"Güncellenmeden geçen saat: {hours:.1f}\n"
    )
    response = await gemini_service.generate(
        prompt,
        system=load_prompt("logistics_analysis"),
        structured_schema={"type": "logistics_risk"},
        temperature=0.1,
    )

    structured = response.structured or {}
    risk_score = float(structured.get("risk_score", 0.5))
    risk_level = str(structured.get("risk_level", "medium"))

    shipment.risk_score = risk_score
    shipment.ai_summary = structured.get("reason")
    if risk_level in ("high", "critical"):
        shipment.status = ShipmentStatus.DELAYED
        # Emit an alert that the dashboard will surface.
        db.add(
            Alert(
                title=f"Kargo riski: {shipment.tracking_code}",
                message=structured.get("reason", "Kargo gecikmesi tespit edildi."),
                category="logistics",
                severity=AlertSeverity.HIGH if risk_level == "high" else AlertSeverity.CRITICAL,
                source="ai",
                related_entity=f"shipment:{shipment.id}",
            )
        )

    await db.commit()
    await db.refresh(shipment)

    return ShipmentAIAnalysis(
        tracking_code=shipment.tracking_code,
        risk_level=risk_level,
        risk_score=risk_score,
        reason=str(structured.get("reason", "")),
        recommended_action=str(structured.get("recommended_action", "")),
        confidence_score=float(structured.get("confidence_score", response.confidence)),
    )


@router.post("/{shipment_id}/events")
async def push_event(
    shipment_id: int,
    event: str,
    location: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> ShipmentRead:
    shipment = await db.get(Shipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Kargo bulunamadı.")
    db.add(
        ShipmentLog(
            shipment_id=shipment.id, event=event, location=location
        )
    )
    if location:
        shipment.current_location = location
    if event.lower().startswith("teslim"):
        shipment.status = ShipmentStatus.DELIVERED
        shipment.delivered_at = datetime.now(timezone.utc)
    elif "transit" in event.lower():
        shipment.status = ShipmentStatus.IN_TRANSIT
    await db.commit()
    await db.refresh(shipment, ["logs"])
    return ShipmentRead.model_validate(shipment)


def _new_tracking_code() -> str:
    return "KOP" + secrets.token_hex(5).upper()
