"""Dashboard / analytics schemas."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DashboardKPIs(BaseModel):
    total_orders: int
    pending_orders: int
    total_revenue: float
    active_shipments: int
    delayed_shipments: int
    low_stock_products: int
    open_tasks: int
    unread_alerts: int
    operational_risk_score: float
    ai_conversations_today: int


class AIInsight(BaseModel):
    title: str
    summary: str
    severity: str
    confidence: float


class SalesTrendPoint(BaseModel):
    date: str
    orders: int
    revenue: float


class DailyDashboard(BaseModel):
    generated_at: datetime
    executive_summary: str
    kpis: DashboardKPIs
    ai_insights: List[AIInsight]
    top_risks: List[str]
    sales_trend: List[SalesTrendPoint]
    inventory_alerts: List[str]
    today_action_items: List[str]
