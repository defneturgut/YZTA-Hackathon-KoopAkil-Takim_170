"""Operations agent — multi-tool reasoning + structured outputs.

Orchestrates the four AI tools, the Gemini service, and produces a
daily operations dashboard. Surfaces two high-level entry points:

    * ``run(query, db)`` — interactive Q&A from the chat / agent page.
    * ``daily_briefing(db)`` — scheduled morning summary for managers.

Both return Pydantic-friendly dicts so the API layer can serialise
them directly.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import load_prompt
from app.ai.services.gemini_service import GeminiResponse, gemini_service
from app.ai.tools import (
    analytics_tool,
    inventory_tool,
    shipment_tool,
    task_tool,
)

logger = logging.getLogger("aegis.ai.agents.operations")


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
def _bind_tools(db: AsyncSession) -> Dict[str, Callable[..., Awaitable[Any]]]:
    """Bind the active DB session to each tool's first argument."""
    return {
        "inventory_tool": lambda **kw: inventory_tool(db, **kw),
        "shipment_tool": lambda **kw: shipment_tool(db, **kw),
        "analytics_tool": lambda **kw: analytics_tool(db, **kw),
        "task_tool": lambda **kw: task_tool(db, **kw),
    }


# -------------------------------------------------------------------------
# Public agent surface
# -------------------------------------------------------------------------
class OperationsAgent:
    """Reasoning agent over the four operational tools."""

    SYSTEM_PROMPT = load_prompt("operations_agent") or (
        "Aegis-KOBİ operasyon AI ajanısın."
    )

    async def run(
        self,
        query: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        tools = _bind_tools(db)
        response: GeminiResponse = await gemini_service.call_with_tools(
            query,
            tools,
            system=self.SYSTEM_PROMPT,
        )
        return {
            "message": response.text,
            "confidence": response.confidence,
            "tool_calls": response.tool_calls,
            "latency_ms": response.latency_ms,
            "model": response.model,
        }

    async def daily_briefing(self, db: AsyncSession) -> Dict[str, Any]:
        """Compose the morning briefing called by the daily scheduler."""
        # Run all four tools in deliberate order to compose a rich summary.
        inventory = await inventory_tool(db, only_critical=False)
        shipments = await shipment_tool(db, only_at_risk=False)
        analytics = await analytics_tool(db)
        tasks = await task_tool(db, action="list")

        # Compose risk view.
        top_risks: List[str] = []
        if analytics["delayed_shipments"] > 0:
            top_risks.append(
                f"{analytics['delayed_shipments']} kargo gecikme/istisna durumunda."
            )
        if analytics["low_stock_products"] > 0:
            top_risks.append(
                f"{analytics['low_stock_products']} ürün kritik stok eşiğinin altında."
            )
        if analytics["pending_orders"] > 0:
            top_risks.append(
                f"{analytics['pending_orders']} sipariş hazırlık bekliyor."
            )
        if not top_risks:
            top_risks.append("Bugün için belirgin bir risk tespit edilmedi.")

        inventory_alerts = [
            f"{p['name']} ({p['sku']}): kalan {p['stock_qty']} {p['unit']}"
            for p in inventory["critical_items"]
        ]

        # Today's action items mix tasks + AI-generated suggestions.
        action_items: List[str] = []
        for s in shipments["at_risk_shipments"][:3]:
            action_items.append(
                f"Kargo {s['tracking_code']} için müşteriye proaktif bilgilendirme gönderilsin."
            )
        for p in inventory["critical_items"][:3]:
            action_items.append(
                f"{p['name']} ({p['sku']}) için tedarikçi siparişi oluşturulsun."
            )
        for t in tasks["tasks"][:3]:
            action_items.append(f"Görev: {t['title']} ({t['priority']})")

        # Compose executive summary via Gemini.
        summary_prompt = (
            "Aşağıdaki günlük operasyon verilerini özetleyen, 3 cümleyi geçmeyen "
            "kurumsal Türkçe bir yönetici özeti üret.\n\n"
            f"Sipariş sayısı (son 14 gün): {analytics['total_orders']}\n"
            f"Toplam gelir: {analytics['total_revenue']} TL\n"
            f"Geciken kargo: {analytics['delayed_shipments']}\n"
            f"Kritik stok: {analytics['low_stock_products']}\n"
            f"Açık görev: {tasks['open_tasks']}\n"
            f"Operasyonel risk skoru: {analytics['operational_risk_score']}\n"
        )
        summary_resp = await gemini_service.generate(
            summary_prompt, system=self.SYSTEM_PROMPT, temperature=0.2
        )

        # Three AI-insight cards.
        ai_insights: List[Dict[str, Any]] = []
        if analytics["delayed_shipments"]:
            ai_insights.append(
                {
                    "title": "Kargo Risk Analizi",
                    "summary": (
                        f"{analytics['delayed_shipments']} kargo gecikme/istisna durumunda. "
                        "Müşteri memnuniyetini korumak için proaktif bildirim önerilir."
                    ),
                    "severity": "high",
                    "confidence": 0.91,
                }
            )
        if analytics["low_stock_products"]:
            ai_insights.append(
                {
                    "title": "Envanter Uyarısı",
                    "summary": (
                        f"{analytics['low_stock_products']} ürün eşik altına düştü. "
                        "Son satış trendine göre 5-7 gün içinde stoksuz kalma riski mevcut."
                    ),
                    "severity": "medium",
                    "confidence": 0.86,
                }
            )
        ai_insights.append(
            {
                "title": "Satış Trendi",
                "summary": (
                    f"Son {analytics['window_days']} günde {analytics['total_orders']} "
                    f"sipariş, {analytics['total_revenue']} TL ciro. Operasyonel risk skoru "
                    f"{analytics['operational_risk_score']}."
                ),
                "severity": "info",
                "confidence": 0.93,
            }
        )

        return {
            "generated_at": datetime.now(timezone.utc),
            "executive_summary": summary_resp.text,
            "kpis": {
                "total_orders": analytics["total_orders"],
                "pending_orders": analytics["pending_orders"],
                "total_revenue": analytics["total_revenue"],
                "active_shipments": shipments["active_shipments"],
                "delayed_shipments": analytics["delayed_shipments"],
                "low_stock_products": analytics["low_stock_products"],
                "open_tasks": tasks["open_tasks"],
                "unread_alerts": 0,  # filled by router from DB
                "operational_risk_score": analytics["operational_risk_score"],
                "ai_conversations_today": 0,  # filled by router
            },
            "ai_insights": ai_insights,
            "top_risks": top_risks,
            "sales_trend": analytics["sales_trend"],
            "inventory_alerts": inventory_alerts,
            "today_action_items": action_items,
        }


operations_agent = OperationsAgent()
