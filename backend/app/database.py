"""Async SQLAlchemy 2.0 engine + session factory.

Supports both PostgreSQL (production via docker-compose) and SQLite
(zero-config demo). The dependency ``get_db`` yields an
``AsyncSession`` to FastAPI routes.
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from app.config import settings


class Base(DeclarativeBase):
    """Base for all ORM models."""


# Engine — pool_pre_ping protects against stale connections in long-lived
# deployments; for SQLite we add ``check_same_thread`` workaround.
_connect_args: dict = {}
if settings.database_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
    connect_args=_connect_args,
)

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a per-request async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (used on startup for the demo).

    Production deployments should rely on Alembic migrations instead.
    """
    # Import here to avoid circular imports at module load.
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
