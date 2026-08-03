"""
Database setup: async engine, session factory, and a shared declarative
Base with common columns (id, created_at, updated_at) that every model
inherits, so you don't redeclare them per-entity.
"""

from datetime import datetime, timezone
from sqlalchemy import DateTime, Integer
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from core.config import settings

engine = create_async_engine(settings.SQLALCHEMY_DATABASE_URI)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Shared declarative base. Every domain model inherits from this,
    not from DeclarativeBase directly, so common columns stay consistent."""

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


async def get_db():
    """FastAPI dependency — yields a session, commits on success, rolls
    back on exception. This is where the commit boundary lives for a
    single request, so multiple repo calls in one request are atomic."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
