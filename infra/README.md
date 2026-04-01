# Infrastructure (Phase 2 + Phase 10 gateway)

Docker Compose stacks PostgreSQL, Redis, the FastAPI backend, the Vite dev server, and an **nginx gateway** (Phase 10).

From the **repository root**:

```bash
docker compose -f infra/docker-compose.yml up --build
```

- **Gateway (recommended):** `http://localhost:8080` — same-origin UI + `/v1` API + WebSocket (`/v1/ws`)
- API (direct): `http://localhost:8000` (e.g. `GET /v1/health`)
- UI (direct): `http://localhost:5173`
- Postgres: `localhost:5432` (user/password/db: `quantedge`)
- Redis: `localhost:6379`

Stop with `Ctrl+C`, then `docker compose -f infra/docker-compose.yml down` (add `-v` to remove the Postgres volume).
