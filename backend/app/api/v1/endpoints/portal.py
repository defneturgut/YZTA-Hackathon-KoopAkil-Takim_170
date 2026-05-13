"""Customer-facing portal endpoints.

Müşteri rolüne sahip kullanıcılar yalnızca *kendi* siparişlerini ve
*kendi* kargolarını görür. Eşleştirme, `Order.customer_email` ile giriş
yapan kullanıcının e-postası üzerinden yapılır — bu hackathon
demonstrasyonu için yeterli olan en sade kurumsal modeldir; production'da
``Order.customer_user_id`` foreign key tercih edilmelidir.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_user
from app.database import get_db
from app.models.order import Order
from app.models.shipment import Shipment
from app.models.user import User

router = APIRouter()


@router.get("/my-orders")
async def my_orders(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[dict]:
    """Return the orders that belong to the logged-in customer."""
    stmt = (
        select(Order)
        .where(Order.customer_email == user.email)
        .options(selectinload(Order.items), selectinload(Order.shipments))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(stmt)
    out: List[dict] = []
    for o in result.scalars().all():
        out.append(
            {
                "id": o.id,
                "order_code": o.order_code,
                "status": o.status.value,
                "total_amount": o.total_amount,
                "shipping_city": o.shipping_city,
                "shipping_address": o.shipping_address,
                "created_at": o.created_at,
                "items_count": len(o.items),
                "tracking_codes": [s.tracking_code for s in o.shipments],
            }
        )
    return out


@router.get("/my-shipments")
async def my_shipments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> List[dict]:
    """Return shipments linked to the logged-in customer's orders."""
    order_q = await db.execute(
        select(Order.id).where(Order.customer_email == user.email)
    )
    order_ids = [row[0] for row in order_q.all()]
    if not order_ids:
        return []
    stmt = (
        select(Shipment)
        .where(Shipment.order_id.in_(order_ids))
        .options(selectinload(Shipment.logs))
        .order_by(Shipment.created_at.desc())
    )
    result = await db.execute(stmt)
    out: List[dict] = []
    for s in result.scalars().all():
        out.append(
            {
                "id": s.id,
                "tracking_code": s.tracking_code,
                "carrier": s.carrier,
                "status": s.status.value,
                "origin_city": s.origin_city,
                "destination_city": s.destination_city,
                "current_location": s.current_location,
                "estimated_delivery": s.estimated_delivery,
                "delivered_at": s.delivered_at,
                "created_at": s.created_at,
                "logs": [
                    {
                        "event": log.event,
                        "location": log.location,
                        "note": log.note,
                        "created_at": log.created_at,
                    }
                    for log in s.logs
                ],
            }
        )
    return out


@router.get("/track/{tracking_code}")
async def public_track(
    tracking_code: str, db: AsyncSession = Depends(get_db)
) -> dict:
    """Public tracking endpoint — no auth required.

    Anyone with a tracking code can see the carrier-level status; sensitive
    fields (customer address, order amount) are intentionally omitted.
    """
    stmt = (
        select(Shipment)
        .options(selectinload(Shipment.logs))
        .where(Shipment.tracking_code == tracking_code)
    )
    result = await db.execute(stmt)
    shipment = result.scalar_one_or_none()
    if not shipment:
        raise HTTPException(status_code=404, detail="Bu takip kodu bulunamadı.")
    return {
        "tracking_code": shipment.tracking_code,
        "carrier": shipment.carrier,
        "status": shipment.status.value,
        "destination_city": shipment.destination_city,
        "current_location": shipment.current_location,
        "estimated_delivery": shipment.estimated_delivery,
        "delivered_at": shipment.delivered_at,
        "logs": [
            {
                "event": log.event,
                "location": log.location,
                "created_at": log.created_at,
            }
            for log in shipment.logs
        ],
    }
