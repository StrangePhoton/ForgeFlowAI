# Local development

## Prerequisites

- Python 3.12 or later (3.13 is fine on the host)
- Docker Engine with Compose v2
- Optional: GNU Make

## Environment

Copy `.env.example` to `.env` and adjust if needed. Compose uses the same variable names. Do not commit `.env`.

The API reads:

- `DATABASE_URL` — SQLAlchemy URL (asyncpg driver added automatically when missing)
- `FORGEFLOW_ENVIRONMENT`, `FORGEFLOW_LOG_LEVEL`, `FORGEFLOW_LOG_JSON`, `FORGEFLOW_API_PREFIX`
- `LLM_*` — reserved for Milestone 3; changing them has no runtime effect yet

Default Compose credentials (`forgeflow` / `forgeflow`) are local-only.

## One-command core stack

```bash
docker compose up --build
```

This starts:

| Service | Port | Role |
| --- | --- | --- |
| `postgres` | 5432 | PostgreSQL 16 with pgvector |
| `api` | 8000 | FastAPI; runs `alembic upgrade head` on start |

Verify:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
```

Expected health payload includes `"status": "healthy"`. Ready returns `"status": "ready"` once Postgres accepts connections.

Stop with `docker compose down`. Add `-v` only if you intend to delete the database volume.

## API on the host, database in Docker

```bash
docker compose up postgres -d
python -m venv .venv
# Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
alembic upgrade head
uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

`DATABASE_URL` should point at `localhost` in this mode, which is the `.env.example` default.

## Quality checks

```bash
ruff check forgeflow apps tests
ruff format --check forgeflow apps tests
mypy forgeflow apps
pytest
```

`tests/integration` talks to PostgreSQL when it is reachable and skips otherwise.

## Migrations

```bash
alembic upgrade head
alembic revision -m "describe the change"
```

Do not put credentials in `alembic.ini`. The env script reads `DATABASE_URL` through application settings.

## Frontend, Ollama, Prometheus, Grafana

Not part of Milestone 0. Compose does not start those services yet.
