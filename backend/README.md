# QuantEdge AI — Backend

Python 3.11+ FastAPI service.

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"
```

## Commands

| Task | Command |
|------|---------|
| Run API | `uvicorn quantedge_backend.main:app --reload --host 0.0.0.0 --port 8000` |
| Lint | `ruff check src tests alembic` |
| Format | `ruff format src tests alembic` |
| Typecheck | `mypy src` |
| Tests | `pytest` |

Run from the `backend` directory with the virtualenv active (package is installed editable from `src/`).
