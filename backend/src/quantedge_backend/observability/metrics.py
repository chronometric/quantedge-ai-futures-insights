"""Lightweight counters (Prometheus text exposition)."""

from __future__ import annotations

import threading

_lock = threading.Lock()
_counts: dict[str, int] = {
    "quantedge_http_requests_total": 0,
    "quantedge_insights_generated_total": 0,
    "quantedge_ws_messages_sent_total": 0,
    "quantedge_pipeline_bars_emitted_total": 0,
    "quantedge_rate_limit_exceeded_total": 0,
    "quantedge_api_key_rejected_total": 0,
}


def inc(name: str, delta: int = 1) -> None:
    with _lock:
        _counts[name] = _counts.get(name, 0) + delta


def snapshot() -> dict[str, int]:
    with _lock:
        return dict(_counts)


def prometheus_text() -> str:
    with _lock:
        lines: list[str] = []
        for k, v in sorted(_counts.items()):
            lines.append(f"# TYPE {k} counter")
            lines.append(f"{k} {v}")
        return "\n".join(lines) + "\n"
