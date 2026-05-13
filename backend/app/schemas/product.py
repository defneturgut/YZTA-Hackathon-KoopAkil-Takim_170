"""Product + inventory schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.product import MovementType


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    category: str = "genel"
    description: Optional[str] = None
    unit: str = "adet"
    price: float = Field(ge=0)
    cost: float = Field(ge=0, default=0)
    stock_qty: float = Field(ge=0, default=0)
    reorder_threshold: float = Field(ge=0, default=10)
    reorder_quantity: float = Field(ge=0, default=50)
    supplier_name: Optional[str] = None
    supplier_email: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    cost: Optional[float] = None
    stock_qty: Optional[float] = None
    reorder_threshold: Optional[float] = None
    reorder_quantity: Optional[float] = None
    supplier_name: Optional[str] = None
    supplier_email: Optional[str] = None


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_low_stock: bool
    created_at: datetime
    updated_at: datetime


class InventoryAdjustment(BaseModel):
    quantity: float
    movement_type: MovementType
    note: Optional[str] = None
