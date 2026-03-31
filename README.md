# QuantEdge AI – Real-Time Futures Insights Engine

Real-time futures analytics platform: streaming OHLCV, deterministic technical context, and RAG-grounded LLM insights exposed via FastAPI and a React dashboard.

**Alternate branding:** `quantedge-llm-trading-system` when emphasizing the LLM stack.

## Repository layout (Phase 1)

| Path | Purpose |
|------|---------|
| `docs/` | Architecture and API narrative |
| `contracts/` | JSON Schemas for bars, market features, and insight payloads |
| `openapi/` | Machine-readable API draft |
| `backend/` | Python FastAPI services (Phase 2+) |
| `frontend/` | React + TypeScript + Vite (Phase 2+) |
| `infra/` | Docker Compose and deployment assets (Phase 2+) |

## Documentation

- [System architecture](docs/architecture.md) — logical diagram, tech choices, environments
- [API contract draft](docs/api-contract.md) — REST and WebSocket message shapes
- [Data contracts](contracts/README.md) — JSON Schema files

## Environment variables

Copy `.env.example` to `.env` for local development (never commit secrets).

## License

Specify license in Phase 2 as needed.
