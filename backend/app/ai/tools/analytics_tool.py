"""Analytics tool — sales trend + operational risk for the agent."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.models.product import Product
from app.models.shipment import Shipment, ShipmentStatus


async def analytics_tool(
    db: AsyncSession,
    *,
    days: int = 14,
) -> Dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    # ----- Sales trend (daily orders + revenue) ------------------------
    orders_q = await db.execute(
        select(Order).where(Order.created_at >= since)
    )
    orders = orders_q.scalars().all()

    by_day: Dict[str, Dict[str, float]] = {}
    for o in orders:
        key = o.created_at.strftime("%Y-%m-%d")
        bucket = by_day.setdefault(key, {"orders": 0, "revenue": 0.0})
        bucket["orders"] += 1
        bucket["revenue"] += float(o.total_amount or 0)
    sales_trend: List[Dict[str, Any]] = [
        {"date": d, "orders": int(v["orders"]), "revenue": round(v["revenue"], 2)}
        for d, v in sorted(by_day.items())
    ]

    # ----- Aggregate KPIs ---------------------------------------------
    total_orders = len(orders)
    total_revenue = round(sum(float(o.total_amount or 0) for o in orders), 2)
    pending_orders = sum(1 for o in orders if o.status == OrderStatus.PENDING)

    low_stock_q = await db.execute(
        select(func.count(Product.id)).where(Product.stock_qty <= Product.reorder_threshold)
    )
    low_stock_count = int(low_stock_q.scalar() or 0)

    delayed_q = await db.execute(
        select(func.count(Shipment.id)).where(
            Shipment.status.in_((ShipmentStatus.DELAYED, ShipmentStatus.EXCEPTION))
        )
    )
    delayed_shipments = int(delayed_q.scalar() or 0)

    # Naive operational risk score: weighted blend of pain points.
    operational_risk = min(
        1.0,
        0.4 * (delayed_shipments / max(1, total_orders or 1))
        + 0.4 * (low_stock_count / 20.0)
        + 0.2 * (pending_orders / max(1, total_orders or 1)),
    )

    return {
        "window_days": days,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
        "pending_orders": pending_orders,
        "delayed_shipments": delayed_shipments,
        "low_stock_products": low_stock_count,
        "operational_risk_score": round(operational_risk, 2),
        "sales_trend": sales_trend,
    }
