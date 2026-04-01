# QuantEdge AI

**Real-time futures insights engine** — ingest and aggregate OHLCV, compute deterministic market context, and generate **RAG-grounded, schema-valid LLM insights**. The stack exposes a **FastAPI** backend (REST + WebSocket), a **React** dashboard, and optional **nginx** gateway for same-origin deployment.

*Alternate product name:* `quantedge-llm-trading-system` (when emphasizing the LLM/RAG layer).

---

## Overview

QuantEdge AI is built for teams that need a **repeatable pipeline** from market bars to structured analytics and narrative insights: durable storage (PostgreSQL), hot cache (Redis), vector retrieval over a methodology knowledge base (Chroma), and observability (structured logs, Prometheus-style metrics). Development defaults use **mock market data** so the full stack runs without external market feeds.

---

## Capabilities

| Area | What you get |
|------|----------------|
| **Market data** | Mock 1m → 5m aggregation pipeline; REST history and live WebSocket bars (`/v1/ws`) |
| **Features** | Deterministic snapshot (regimes, levels, etc.) for charting and LLM context |
| **Insights** | On-demand `POST /v1/insights`; optional streaming when bars complete (configurable) |
| **RAG** | KB chunking, embedding retrieval, OpenAI chat with JSON output (mock path when no key) |
| **Ops** | Health/ready probes, correlation IDs, optional API key + rate limits on expensive routes |
| **Database** | Alembic migrations on PostgreSQL; SQLite used for automated tests |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| API | Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2 (async), Redis, Alembic |
| UI | React 19, TypeScript (strict), Vite, Recharts |
| Data | PostgreSQL 16 (Compose), Redis 7 |
| Infra | Docker Compose, nginx (optional single entry on `:8080`) |

---

## Prerequisites

- **Docker Desktop** (or compatible engine) for Compose — *recommended* for full stack
- **Without Docker:** Python **3.11+**, **Node.js 22+**, local PostgreSQL and Redis if you run the backend against real services

---

## Quick start (Docker Compose)

From the **repository root**:

```bash
docker compose -f infra/docker-compose.yml up --build
```

When services are healthy:

| Entry point | URL | Notes |
|-------------|-----|--------|
| **Gateway** (recommended) | [http://localhost:8080](http://localhost:8080) | Same-origin UI, `/v1` REST, WebSocket `/v1/ws` |
| API only | [http://localhost:8000](http://localhost:8000) | e.g. `GET /v1/health`, `/docs` (Swagger) |
| UI only (Vite) | [http://localhost:5173](http://localhost:5173) | Dev server; proxies `/v1` to API when using relative URLs |
| PostgreSQL | `localhost:5432` | User / password / database: `quantedge` |
| Redis | `localhost:6379` | DB `0` in default Compose env |

Stop: `Ctrl+C`, then:

```bash
docker compose -f infra/docker-compose.yml down
```

Add `-v` to remove named volumes (e.g. Postgres data). See [infra/README.md](infra/README.md) for gateway behavior and ports.

---

## Local development (without Compose)

1. **Environment** — Copy `.env.example` to `.env` at the repo root (and/or `frontend/.env` for Vite-specific vars). Never commit secrets.

2. **Backend** — See [backend/README.md](backend/README.md): editable install, Uvicorn on port **8000**, run tests with `pytest`.

3. **Frontend** — See [frontend/README.md](frontend/README.md): `npm install`, `npm run dev` on port **5173**. With an empty `VITE_API_BASE_URL`, the dev server proxies `/v1` (and API docs paths) to `http://localhost:8000`.

4. **Services** — Point `DATABASE_URL` and `REDIS_URL` in `.env` at your local PostgreSQL and Redis if not using Docker for those alone.

---

## Configuration (high level)

- **`.env.example`** documents variables for logging, CORS, market symbols, mock pipeline, RAG, WebSocket streaming, API keys, rate limits, Alembic, and frontend `VITE_*` settings.
- **CORS** must include any browser origin you use (e.g. `http://localhost:5173`, `http://localhost:8080` when using the gateway).

---

## API

- **Live docs (Swagger):** `http://localhost:8000/docs` (or via gateway / Vite proxy)
- **OpenAPI draft (repo):** [openapi/openapi.yaml](openapi/openapi.yaml)
- **Contract narrative:** [docs/api-contract.md](docs/api-contract.md)

---

## Repository layout

| Path | Purpose |
|------|---------|
| [docs/](docs/) | Architecture and API narrative |
| [contracts/](contracts/) | JSON Schemas (bars, features, insights) |
| [openapi/](openapi/) | OpenAPI draft |
| [backend/](backend/) | FastAPI application and Alembic migrations |
| [frontend/](frontend/) | React dashboard |
| [infra/](infra/) | Docker Compose, nginx gateway config |
| [.github/workflows/](.github/workflows/) | CI: lint, tests, typecheck, Docker image builds |

---

## Quality checks (CI)

The default pipeline runs **Ruff** (lint + format), **mypy** on the backend, **pytest**, **Alembic** history validation, frontend **Prettier + ESLint + production build**, and **Docker builds** for backend and frontend images. Run the same commands locally before pushing; see [backend/README.md](backend/README.md) and [frontend/README.md](frontend/README.md).

---

## Documentation

- [System architecture](docs/architecture.md)
- [API contract draft](docs/api-contract.md)
- [Data contracts](contracts/README.md)

---

## License

Specify a license before public distribution.
