"""Application settings (environment-driven)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="dev", alias="APP_ENV")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    database_url: str = Field(
        default="postgresql+asyncpg://quantedge:quantedge@localhost:5432/quantedge",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

    cors_origins: str = Field(
        default="http://localhost:5173",
        alias="CORS_ORIGINS",
    )

    market_symbols: str = Field(default="ES,NQ", alias="MARKET_SYMBOLS")
    mock_market_data: bool = Field(default=True, alias="MOCK_MARKET_DATA")
    mock_tick_seconds: float = Field(default=0.25, alias="MOCK_TICK_SECONDS", ge=0.05)
    retention_months: int = Field(default=6, alias="RETENTION_MONTHS", ge=1, le=120)

    testing: bool = Field(default=False, alias="TESTING")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    chroma_persist_dir: str = Field(default=".chroma", alias="CHROMA_PERSIST_DIR")
    rag_embedding_model: str = Field(default="text-embedding-3-small", alias="RAG_EMBEDDING_MODEL")
    rag_chat_model: str = Field(default="gpt-4o-mini", alias="RAG_CHAT_MODEL")
    rag_top_k: int = Field(default=5, alias="RAG_TOP_K", ge=1, le=20)
    kb_version: str = Field(default="1.0.0", alias="KB_VERSION")
    kb_dir: str = Field(default="kb", alias="KB_DIR")
    rag_mock_insights: bool = Field(default=False, alias="RAG_MOCK_INSIGHTS")

    log_json: bool = Field(default=False, alias="LOG_JSON")
    ws_broadcast_enabled: bool = Field(default=True, alias="WS_BROADCAST_ENABLED")
    stream_insights_on_bar: bool = Field(default=True, alias="STREAM_INSIGHTS_ON_BAR")

    api_key: str | None = Field(default=None, alias="API_KEY")
    insights_rate_limit_per_minute: int = Field(
        default=30,
        alias="INSIGHTS_RATE_LIMIT_PER_MINUTE",
        ge=0,
        le=100_000,
    )

    @field_validator("market_symbols")
    @classmethod
    def strip_symbols(cls, v: str) -> str:
        return v.strip()

    def symbol_list(self) -> list[str]:
        return [s.strip().upper() for s in self.market_symbols.split(",") if s.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def clear_settings_cache() -> None:
    get_settings.cache_clear()
