"""LLM / RAG insight endpoint."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from quantedge_backend.api.deps import get_session
from quantedge_backend.llm.insight_service import generate_insight
from quantedge_backend.settings import Settings, get_settings

router = APIRouter(prefix="/v1", tags=["insights"])


class InsightRequest(BaseModel):
    symbol: str = Field(..., min_length=1)
    interval: str = Field(default="5m", pattern=r"^[0-9]+[mhd]$")
    include_narrative: bool = True
    lookback: int = Field(default=120, ge=55, le=500)


@router.post("/insights")
async def post_insight(
    body: InsightRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, Any]:
    """RAG over KB + market snapshot; returns schema-shaped insight JSON."""
    try:
        return await generate_insight(
            session,
            settings,
            symbol=body.symbol,
            interval=body.interval,
            lookback=body.lookback,
            include_narrative=body.include_narrative,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
