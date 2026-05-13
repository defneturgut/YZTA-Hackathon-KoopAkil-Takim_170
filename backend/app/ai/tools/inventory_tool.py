"""Inventory tool — exposes stock state to the operations agent."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def inventory_tool(
    db: AsyncSession,
    *,
    only_critical: bool = False,
    limit: int = 50,
    query: Optional[str] = None,
) -> Dict[str, Any]:
    """Return stock snapshot, optionally filtered to critical items.

    Args:
        only_critical: Yalnızca yeniden-sipariş eşiğinin altındaki ürünleri döner.
        limit: Toplam satır sınırı (büyük katalog için).
        query: Tek bir ürünü ön plana çıkarmak için arama metni. Eşleşen
            ürünler ``matches`` listesinde döner — Gemini bunu kullanarak
            "Defne sabunundan 9 paket kaldı." gibi spesifik cevaplar üretir.
    """
    stmt = select(Product).order_by(Product.stock_qty.asc()).limit(limit)
    result = await db.execute(stmt)
    products = result.scalars().all()

    items: List[Dict[str, Any]] = []
    critical: List[Dict[str, Any]] = []
    for p in products:
        entry = {
            "sku": p.sku,
            "name": p.name,
            "stock_qty": p.stock_qty,
            "unit": p.unit,
            "reorder_threshold": p.reorder_threshold,
            "is_low_stock": p.is_low_stock,
            "supplier_name": p.supplier_name,
            "price": p.price,
            "category": p.category,
        }
        items.append(entry)
        if p.is_low_stock:
            critical.append(entry)

    # Ürün adı eşleşmesi — Gemini'nin spesifik sorulara yanıt vermesi için.
    matches: List[Dict[str, Any]] = []
    if query:
        q = query.lower()
        # Türkçe karakter ve "ı/i" duyarsızlığı için basit normalize
        for it in items:
            haystack = f"{it['name']} {it['sku']} {it['category']}".lower()
            # Sorgudaki anlamlı kelimeleri 3+ char olarak parçala
            tokens = [t for t in q.split() if len(t) >= 3]
            if any(t in haystack for t in tokens):
                matches.append(it)

    if only_critical:
        items = critical

    return {
        "total_products_inspected": len(items),
        "critical_count": len(critical),
        "items": items,
        "critical_items": critical[:10],
        "matches": matches[:5],
        "matched_query": query,
    }
