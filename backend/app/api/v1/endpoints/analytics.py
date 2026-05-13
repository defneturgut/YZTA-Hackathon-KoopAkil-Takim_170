"""Analytics endpoints — sales trend, inventory snapshot, shipping risk.

Tüm uç noktalar hataya dayanıklıdır; herhangi bir tool patladığında bile
boş ama valid bir payload döner — UI grafiklerinin boş ekran göstermesi
yerine "veri yok" eyaletini düzgün render etmesini sağlar.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.tools.analytics_tool import analytics_tool
from app.ai.tools.inventory_tool import inventory_tool
from app.ai.tools.shipment_tool import shipment_tool
from app.database import get_db

logger = logging.getLogger("koopakil.api.analytics")
router = APIRouter()


@router.get("/sales")
async def sales_analytics(
    days: int = 14, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    try:
        return await analytics_tool(db, days=days)
    except Exception:  # noqa: BLE001
        logger.exception("analytics_tool failed")
        return {
            "window_days": days,
            "total_orders": 0,
            "total_revenue": 0.0,
            "pending_orders": 0,
            "delayed_shipments": 0,
            "low_stock_products": 0,
            "operational_risk_score": 0.0,
            "sales_trend": [],
        }


@router.get("/inventory")
async def inventory_analytics(
    only_critical: bool = False, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    try:
        return await inventory_tool(db, only_critical=only_critical)
    except Exception:  # noqa: BLE001
        logger.exception("inventory_tool failed")
        return {
            "total_products_inspected": 0,
            "critical_count": 0,
            "items": [],
            "critical_items": [],
        }


@router.get("/shipping")
async def shipping_analytics(
    only_at_risk: bool = False, db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    try:
        return await shipment_tool(db, only_at_risk=only_at_risk)
    except Exception:  # noqa: BLE001
        logger.exception("shipment_tool failed")
        return {
            "active_shipments": 0,
            "at_risk_count": 0,
            "shipments": [],
            "at_risk_shipments": [],
        }
