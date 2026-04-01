"""OHLCV persistence and retention."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast

from sqlalchemy import and_, delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from quantedge_backend.db.models import OhlcvBar
from quantedge_backend.market.types import FiveMinuteBar


async def upsert_five_minute_bar(
    session: AsyncSession,
    *,
    symbol: str,
    interval: str,
    bar: FiveMinuteBar,
    source: str | None,
) -> OhlcvBar:
    """Insert or replace a 5m bar row."""
    existing = await session.scalar(
        select(OhlcvBar).where(
            OhlcvBar.symbol == symbol.upper(),
            OhlcvBar.interval == interval,
            OhlcvBar.time_open == bar.time_open,
        ),
    )
    if existing is not None:
        existing.time_close = bar.time_close
        existing.open = bar.open
        existing.high = bar.high
        existing.low = bar.low
        existing.close = bar.close
        existing.volume = bar.volume
        existing.source = source
        await session.flush()
        return existing

    row = OhlcvBar(
        symbol=symbol.upper(),
        interval=interval,
        time_open=bar.time_open,
        time_close=bar.time_close,
        open=bar.open,
        high=bar.high,
        low=bar.low,
        close=bar.close,
        volume=bar.volume,
        source=source,
    )
    session.add(row)
    await session.flush()
    return row


async def list_bars(
    session: AsyncSession,
    *,
    symbol: str,
    interval: str,
    start: datetime | None,
    end: datetime | None,
    limit: int,
) -> list[OhlcvBar]:
    conds = [
        OhlcvBar.symbol == symbol.upper(),
        OhlcvBar.interval == interval,
    ]
    if start is not None:
        conds.append(OhlcvBar.time_open >= start)
    if end is not None:
        conds.append(OhlcvBar.time_open < end)
    stmt = select(OhlcvBar).where(and_(*conds)).order_by(OhlcvBar.time_open.desc()).limit(limit)
    result = await session.scalars(stmt)
    rows = list(result.all())
    rows.reverse()
    return rows


async def apply_retention(session: AsyncSession, *, retention_months: int) -> int:
    """Delete bars older than retention window."""
    cutoff = datetime.now(UTC) - timedelta(days=30 * retention_months)
    res = await session.execute(delete(OhlcvBar).where(OhlcvBar.time_open < cutoff))
    cr = cast(CursorResult[Any], res)
    rc = cr.rowcount
    return int(rc) if rc is not None else 0


def bar_to_contract_dict(row: OhlcvBar) -> dict[str, Any]:
    """API payload aligned with contracts/ohlcv-bar.schema.json."""
    return {
        "schema_version": "1.0.0",
        "symbol": row.symbol,
        "interval": row.interval,
        "time_open": row.time_open.isoformat().replace("+00:00", "Z"),
        "time_close": row.time_close.isoformat().replace("+00:00", "Z"),
        "open": row.open,
        "high": row.high,
        "low": row.low,
        "close": row.close,
        "volume": row.volume,
        "source": row.source,
    }
