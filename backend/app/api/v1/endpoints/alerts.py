"""System alerts."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertRead

router = APIRouter()


@router.get("", response_model=List[AlertRead])
async def list_alerts(
    unread_only: bool = False, db: AsyncSession = Depends(get_db)
) -> List[AlertRead]:
    stmt = select(Alert).order_by(Alert.created_at.desc()).limit(100)
    if unread_only:
        stmt = stmt.where(Alert.is_read.is_(False))
    result = await db.execute(stmt)
    return [AlertRead.model_validate(a) for a in result.scalars().all()]


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(
    payload: AlertCreate, db: AsyncSession = Depends(get_db)
) -> AlertRead:
    alert = Alert(**payload.model_dump())
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    return AlertRead.model_validate(alert)


@router.post("/{alert_id}/read", response_model=AlertRead)
async def mark_read(alert_id: int, db: AsyncSession = Depends(get_db)) -> AlertRead:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Uyarı bulunamadı.")
    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return AlertRead.model_validate(alert)


@router.post("/{alert_id}/resolve", response_model=AlertRead)
async def resolve_alert(
    alert_id: int, db: AsyncSession = Depends(get_db)
) -> AlertRead:
    alert = await db.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Uyarı bulunamadı.")
    alert.is_resolved = True
    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return AlertRead.model_validate(alert)
