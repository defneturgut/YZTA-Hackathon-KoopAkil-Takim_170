"""Inventory endpoints + AI forecast."""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.prompts import load_prompt
from app.ai.services.gemini_service import gemini_service
from app.database import get_db
from app.models.product import InventoryMovement, Product
from app.schemas.product import (
    InventoryAdjustment,
    ProductCreate,
    ProductRead,
    ProductUpdate,
)

router = APIRouter()


@router.get("", response_model=List[ProductRead])
async def list_products(
    only_low_stock: bool = False,
    db: AsyncSession = Depends(get_db),
) -> List[ProductRead]:
    stmt = select(Product).order_by(Product.name)
    if only_low_stock:
        stmt = stmt.where(Product.stock_qty <= Product.reorder_threshold)
    result = await db.execute(stmt)
    return [ProductRead.model_validate(p) for p in result.scalars().all()]


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate, db: AsyncSession = Depends(get_db)
) -> ProductRead:
    exists = await db.execute(select(Product).where(Product.sku == payload.sku))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Bu SKU zaten mevcut.")
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return ProductRead.model_validate(product)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: AsyncSession = Depends(get_db),
) -> ProductRead:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(product, k, v)
    await db.commit()
    await db.refresh(product)
    return ProductRead.model_validate(product)


@router.post("/{product_id}/adjust", response_model=ProductRead)
async def adjust_inventory(
    product_id: int,
    payload: InventoryAdjustment,
    db: AsyncSession = Depends(get_db),
) -> ProductRead:
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")
    movement = InventoryMovement(
        product_id=product.id,
        movement_type=payload.movement_type,
        quantity=payload.quantity,
        note=payload.note,
    )
    delta = payload.quantity if payload.movement_type.value != "outbound" else -payload.quantity
    if payload.movement_type.value == "adjustment":
        product.stock_qty = max(0.0, payload.quantity)
    else:
        product.stock_qty = max(0.0, product.stock_qty + delta)
    db.add(movement)
    await db.commit()
    await db.refresh(product)
    return ProductRead.model_validate(product)


@router.post("/{product_id}/forecast")
async def forecast_inventory(
    product_id: int, db: AsyncSession = Depends(get_db)
) -> dict:
    """AI-powered stock-out forecast + reorder suggestion."""
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Ürün bulunamadı.")

    prompt = (
        f"SKU: {product.sku}\n"
        f"Ürün: {product.name}\n"
        f"Mevcut stok: {product.stock_qty} {product.unit}\n"
        f"Yeniden sipariş eşiği: {product.reorder_threshold} {product.unit}\n"
        f"Önerilen yeniden sipariş miktarı: {product.reorder_quantity} {product.unit}\n"
        "Lütfen tükenme tarihi ve önerilen sipariş miktarını JSON formatında üret."
    )
    response = await gemini_service.generate(
        prompt,
        system=load_prompt("inventory_prediction"),
        structured_schema={"type": "inventory_forecast"},
        temperature=0.2,
    )
    return {
        "product": ProductRead.model_validate(product).model_dump(),
        "forecast": response.structured,
        "ai_text": response.text,
        "confidence": response.confidence,
        "model": response.model,
    }
