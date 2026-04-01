"""SQLAlchemy ORM models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Double, Float, Index, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OhlcvBar(Base):
    """Stored OHLCV candle (e.g. aggregated 5m)."""

    __tablename__ = "ohlcv_bars"
    __table_args__ = (
        UniqueConstraint("symbol", "interval", "time_open", name="uq_ohlcv_symbol_interval_open"),
        Index("ix_ohlcv_symbol_interval_time", "symbol", "interval", "time_open"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(16), nullable=False)
    time_open: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    time_close: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Double, nullable=False)
    high: Mapped[float] = mapped_column(Double, nullable=False)
    low: Mapped[float] = mapped_column(Double, nullable=False)
    close: Mapped[float] = mapped_column(Double, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str | None] = mapped_column(String(64), nullable=True)
