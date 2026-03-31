# Infrastructure (Phase 2)

Docker Compose stacks PostgreSQL, Redis, the FastAPI backend, and the Vite dev server.

From the **repository root**:

```bash
docker compose -f infra/docker-compose.yml up --build
```

- API: `http://localhost:8000` (e.g. `GET /v1/health`)
- UI: `http://localhost:5173`
- Postgres: `localhost:5432` (user/password/db: `quantedge`)
- Redis: `localhost:6379`

Stop with `Ctrl+C`, then `docker compose -f infra/docker-compose.yml down` (add `-v` to remove the Postgres volume).
