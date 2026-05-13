"""Executive dashboard — composed via the operations agent."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents import operations_agent
from app.database import get_db
from app.models.alert import Alert
from app.models.conversation import Conversation
from app.schemas.dashboard import DailyDashboard

logger = logging.getLogger("koopakil.api.dashboard")
router = APIRouter()


@router.get("/daily", response_model=DailyDashboard)
async def daily_dashboard(db: AsyncSession = Depends(get_db)) -> DailyDashboard:
    """Yönetici briefingi. Hata durumunda boş ama valid bir payload döner ki
    dashboard ekranı asla beyaz/boş kalmasın."""
    try:
        briefing = await operations_agent.daily_briefing(db)
    except Exception:  # noqa: BLE001
        logger.exception("daily_briefing crashed — returning safe fallback")
        briefing = _safe_fallback_briefing()

    # Live-stamp counts that the agent could not see (alerts + AI chats today).
    try:
        unread_q = await db.execute(
            select(func.count(Alert.id)).where(Alert.is_read.is_(False))
        )
        unread = int(unread_q.scalar() or 0)
    except Exception:  # noqa: BLE001
        unread = 0

    try:
        today_start = datetime.now(timezone.utc) - timedelta(hours=24)
        convos_q = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.created_at >= today_start
            )
        )
        convos_today = int(convos_q.scalar() or 0)
    except Exception:  # noqa: BLE001
        convos_today = 0

    briefing["kpis"]["unread_alerts"] = unread
    briefing["kpis"]["ai_conversations_today"] = convos_today

    return DailyDashboard.model_validate(briefing)


def _safe_fallback_briefing() -> dict:
    """Use when the agent fails — ensures the UI always renders cleanly."""
    return {
        "generated_at": datetime.now(timezone.utc),
        "executive_summary": (
            "Bugünün özeti şu an üretilemedi. Sistem verileri kontrol ediliyor; "
            "lütfen birkaç dakika sonra tekrar deneyin."
        ),
        "kpis": {
            "total_orders": 0,
            "pending_orders": 0,
            "total_revenue": 0.0,
            "active_shipments": 0,
            "delayed_shipments": 0,
            "low_stock_products": 0,
            "open_tasks": 0,
            "unread_alerts": 0,
            "operational_risk_score": 0.0,
            "ai_conversations_today": 0,
        },
        "ai_insights": [
            {
                "title": "Veri bekleniyor",
                "summary": (
                    "Henüz analiz üretilebilecek yeterli işlem yok ya da "
                    "tool zinciri bir hata verdi."
                ),
                "severity": "info",
                "confidence": 0.5,
            }
        ],
        "top_risks": ["Şu an aktif risk göstergesi yok."],
        "sales_trend": [],
        "inventory_alerts": [],
        "today_action_items": [],
    }
