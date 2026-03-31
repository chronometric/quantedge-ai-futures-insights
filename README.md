# QuantEdge AI – Real-Time Futures Insights Engine

Real-time futures analytics platform: streaming OHLCV, deterministic technical context, and RAG-grounded LLM insights exposed via FastAPI and a React dashboard.

**Alternate branding:** `quantedge-llm-trading-system` when emphasizing the LLM stack.

## Repository layout

| Path | Purpose |
|------|---------|
| `docs/` | Architecture and API narrative |
| `contracts/` | JSON Schemas for bars, market features, and insight payloads |
| `openapi/` | Machine-readable API draft |
| `backend/` | Python 3.11+ FastAPI service |
| `frontend/` | React + TypeScript + Vite |
| `infra/` | Docker Compose (Postgres, Redis, API, UI) |
| `.github/workflows/` | CI (lint, test, Docker builds) |

## Quick start (Phase 2)

### Docker Compose (full stack)

From the repository root:

```bash
docker compose -f infra/docker-compose.yml up --build
```

- **API:** `http://localhost:8000` — try `GET /v1/health`
- **UI:** `http://localhost:5173`
- **Postgres:** `localhost:5432` (user / password / database: `quantedge`)
- **Redis:** `localhost:6379`

See [infra/README.md](infra/README.md) for details.

### Local development (without Docker)

**Backend:** see [backend/README.md](backend/README.md) — create a venv, `pip install -e ".[dev]"`, run Uvicorn on port 8000.

**Frontend:** see [frontend/README.md](frontend/README.md) — `npm install`, `npm run dev`.

Copy `.env.example` to `.env` for local settings (never commit secrets).

## Documentation

- [System architecture](docs/architecture.md)
- [API contract draft](docs/api-contract.md)
- [Data contracts](contracts/README.md)

## License

Specify license as needed before public distribution.
