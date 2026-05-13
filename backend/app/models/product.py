"""Product catalogue + inventory movements (in/out per SKU)."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class MovementType(str, enum.Enum):
    INBOUND = "inbound"     # Tedarikçi → depo
    OUTBOUND = "outbound"   # Satış / sevkiyat
    ADJUSTMENT = "adjustment"  # Sayım düzeltmesi


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False, default="genel")
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    unit: Mapped[str] = mapped_column(String(16), default="adet", nullable=False)  # adet, kg, lt
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    stock_qty: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_threshold: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    reorder_quantity: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)

    supplier_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    supplier_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    movements: Mapped[List["InventoryMovement"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )

    @property
    def is_low_stock(self) -> bool:
        return self.stock_qty <= self.reorder_threshold

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Product {self.sku} stock={self.stock_qty}>"


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    movement_type: Mapped[MovementType] = mapped_column(
        SAEnum(MovementType, native_enum=False, length=16), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    product: Mapped[Product] = relationship(back_populates="movements")
