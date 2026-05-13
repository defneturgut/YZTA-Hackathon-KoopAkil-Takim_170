"""Shipment tool — surfaces in-flight kargolar + anomalies to the agent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shipment import Shipment, ShipmentStatus


_OPEN_STATES = (
    ShipmentStatus.CREATED,
    ShipmentStatus.PICKED_UP,
    ShipmentStatus.IN_TRANSIT,
    ShipmentStatus.AT_HUB,
    ShipmentStatus.OUT_FOR_DELIVERY,
    ShipmentStatus.DELAYED,
    ShipmentStatus.EXCEPTION,
)


async def shipment_tool(
    db: AsyncSession,
    *,
    only_at_risk: bool = False,
    limit: int = 50,
) -> Dict[str, Any]:
    stmt = select(Shipment).where(Shipment.status.in_(_OPEN_STATES)).limit(limit)
    result = await db.execute(stmt)
    shipments = result.scalars().all()

    rows: List[Dict[str, Any]] = []
    at_risk: List[Dict[str, Any]] = []

    for s in shipments:
        hours = _hours_since(s.updated_at)
        is_risky = (
            s.status in (ShipmentStatus.DELAYED, ShipmentStatus.EXCEPTION)
            or hours > 48
            or s.risk_score >= 0.6
        )
        row = {
            "tracking_code": s.tracking_code,
            "carrier": s.carrier,
            "status": s.status.value,
            "destination_city": s.destination_city,
            "current_location": s.current_location,
            "hours_since_update": round(hours, 1),
            "risk_score": s.risk_score,
            "ai_summary": s.ai_summary,
        }
        rows.append(row)
        if is_risky:
            at_risk.append(row)

    if only_at_risk:
        rows = at_risk

    return {
        "active_shipments": len(rows),
        "at_risk_count": len(at_risk),
        "shipments": rows,
        "at_risk_shipments": at_risk[:10],
    }


def _hours_since(dt: datetime | None) -> float:
    if not dt:
        return 0.0
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now(timezone.utc).replace(tzinfo=None)
    return (now - dt).total_seconds() / 3600.0
