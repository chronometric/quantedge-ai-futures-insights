"""Market data endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from quantedge_backend.api.deps import get_market_state, get_session
from quantedge_backend.db.bars_repo import bar_to_contract_dict, list_bars
from quantedge_backend.features.snapshot import MIN_BARS, build_market_features
from quantedge_backend.market.stream import MarketRuntimeState
from quantedge_backend.settings import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["market"])


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None or value == "":
        return None
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


@router.get("/symbols")
def list_symbols(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, list[str]]:
    return {"symbols": settings.symbol_list()}


@router.get("/market/{symbol}/bars")
async def get_bars(
    symbol: str,
    interval: str = Query(..., description="Bar interval, e.g. 5m"),
    start: str | None = Query(None),
    end: str | None = Query(None),
    limit: int = Query(500, ge=1, le=5000),
    *,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, list[dict[str, Any]]]:
    try:
        start_dt = _parse_iso_datetime(start)
        end_dt = _parse_iso_datetime(end)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid datetime: {e}") from e
    rows = await list_bars(
        session,
        symbol=symbol,
        interval=interval,
        start=start_dt,
        end=end_dt,
        limit=limit,
    )
    return {"bars": [bar_to_contract_dict(r) for r in rows]}


@router.get("/market/{symbol}/features")
async def get_market_features(
    symbol: str,
    interval: str = Query(..., description="Bar interval, e.g. 5m"),
    lookback: int = Query(120, ge=MIN_BARS, le=500),
    token_budget: int | None = Query(
        None,
        description="Optional coarse LLM token budget (applies compaction).",
        ge=256,
        le=16000,
    ),
    *,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict[str, Any]:
    """Deterministic technical context (pre-LLM) from recent stored bars."""
    rows = await list_bars(
        session,
        symbol=symbol,
        interval=interval,
        start=None,
        end=None,
        limit=lookback,
    )
    try:
        return build_market_features(
            rows,
            symbol=symbol,
            interval=interval,
            token_budget=token_budget,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/market/status")
async def market_status(
    state: Annotated[MarketRuntimeState, Depends(get_market_state)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """Last completed 5m bar close time per symbol (UTC ISO-8601)."""
    async with state.lock:
        snapshot = dict(state.last_bar_close_utc)
    symbols = settings.symbol_list()
    return {
        "symbols": symbols,
        "last_bar_close_utc": {s: snapshot.get(s) for s in symbols},
    }
