"""UTC time alignment for bar buckets."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

FIVE_MINUTES = timedelta(minutes=5)


def ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def floor_minute_utc(dt: datetime) -> datetime:
    """Floor to the open of the 1-minute bar containing ``dt`` (UTC)."""
    u = ensure_utc(dt)
    return u.replace(second=0, microsecond=0)


def floor_5m_open_utc(dt: datetime) -> datetime:
    """Start of the 5-minute bucket containing ``dt`` (UTC)."""
    u = ensure_utc(dt)
    minute_of_day = u.hour * 60 + u.minute
    floored = (minute_of_day // 5) * 5
    h, m = divmod(floored, 60)
    return u.replace(hour=h, minute=m, second=0, microsecond=0)


def ceil_5m_close_utc(time_open_5m: datetime) -> datetime:
    """Exclusive bar end for a 5m bucket (``time_open`` + 5 minutes)."""
    return ensure_utc(time_open_5m) + FIVE_MINUTES
