"""Phase 8 — optional API key and insight rate limiting."""

from __future__ import annotations

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from quantedge_backend.main import app
from quantedge_backend.settings import clear_settings_cache


def test_insight_401_without_api_key_when_configured(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret-phase8")
    clear_settings_cache()
    try:
        with TestClient(app) as client:
            r = client.post(
                "/v1/insights",
                json={
                    "symbol": "ES",
                    "interval": "5m",
                    "include_narrative": True,
                    "lookback": 120,
                },
            )
        assert r.status_code == 401
        assert r.json()["detail"] == "Invalid or missing API key"
    finally:
        monkeypatch.delenv("API_KEY", raising=False)
        clear_settings_cache()


def test_insight_accepts_x_api_key(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("API_KEY", "test-secret-phase8")
    clear_settings_cache()
    try:
        with TestClient(app) as client:
            r = client.post(
                "/v1/insights",
                json={
                    "symbol": "ES",
                    "interval": "5m",
                    "include_narrative": True,
                    "lookback": 120,
                },
                headers={"X-API-Key": "test-secret-phase8"},
            )
        assert r.status_code != 401
    finally:
        monkeypatch.delenv("API_KEY", raising=False)
        clear_settings_cache()


def test_insight_rate_limit_429(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("INSIGHTS_RATE_LIMIT_PER_MINUTE", "2")
    clear_settings_cache()
    try:
        body = {
            "symbol": "ES",
            "interval": "5m",
            "include_narrative": True,
            "lookback": 120,
        }
        with TestClient(app) as client:
            client.post("/v1/insights", json=body)
            client.post("/v1/insights", json=body)
            r = client.post("/v1/insights", json=body)
        assert r.status_code == 429
        assert "Retry-After" in r.headers
    finally:
        monkeypatch.setenv("INSIGHTS_RATE_LIMIT_PER_MINUTE", "0")
        clear_settings_cache()
