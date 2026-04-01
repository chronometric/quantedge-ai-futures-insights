"""Pytest bootstrap: test env before importing the application."""

from __future__ import annotations

import os

os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["MOCK_MARKET_DATA"] = "false"

from quantedge_backend.settings import clear_settings_cache

clear_settings_cache()
