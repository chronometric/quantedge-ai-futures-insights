"""Redis hot cache for latest and recent bars."""

from __future__ import annotations

import json
from typing import Any, cast

from redis.asyncio import Redis

RECENT_MAX = 50


def _last_key(symbol: str, interval: str) -> str:
    return f"quantedge:last_bar:{symbol.upper()}:{interval}"


def _recent_key(symbol: str, interval: str) -> str:
    return f"quantedge:recent_bars:{symbol.upper()}:{interval}"


async def set_last_bar(redis: Redis, symbol: str, interval: str, payload: dict[str, Any]) -> None:
    await cast(Any, redis).set(_last_key(symbol, interval), json.dumps(payload))


async def push_recent_bar(
    redis: Redis, symbol: str, interval: str, payload: dict[str, Any]
) -> None:
    key = _recent_key(symbol, interval)
    r = cast(Any, redis)
    await r.lpush(key, json.dumps(payload))
    await r.ltrim(key, 0, RECENT_MAX - 1)


async def get_last_bar_json(redis: Redis, symbol: str, interval: str) -> dict[str, Any] | None:
    raw = await cast(Any, redis).get(_last_key(symbol, interval))
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return cast(dict[str, Any], json.loads(raw))
