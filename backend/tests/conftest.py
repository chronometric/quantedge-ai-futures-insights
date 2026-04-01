"""Pytest bootstrap: test env before importing the application."""

from __future__ import annotations

import os
from pathlib import Path

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["MOCK_MARKET_DATA"] = "false"
os.environ["INSIGHTS_RATE_LIMIT_PER_MINUTE"] = "0"
os.environ["CHROMA_PERSIST_DIR"] = str(Path(__file__).resolve().parents[1] / ".chroma_test")

from quantedge_backend.settings import clear_settings_cache

clear_settings_cache()
