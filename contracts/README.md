# Data contracts (JSON Schema)

Shared definitions for **QuantEdge AI** backend, LLM structured output validation, and frontend TypeScript types (generated or hand-mapped in Phase 2+).

| Schema | Description |
|--------|-------------|
| [ohlcv-bar.schema.json](ohlcv-bar.schema.json) | Single 5m (or configured) OHLCV bar from ingestion or API. |
| [market-features.schema.json](market-features.schema.json) | Deterministic features and levels before / alongside LLM. |
| [insight-payload.schema.json](insight-payload.schema.json) | RAG + LLM output for UI overlays and narrative. |

**Draft:** JSON Schema draft 2020-12.  
**Versioning:** Top-level `schema_version` uses SemVer for contract evolution.
