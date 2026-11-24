# Local development

## Prerequisites

- Python 3.12 or later (3.13 is fine on the host)
- Docker Engine with Compose v2
- Optional: GNU Make
- Node.js 22+ for the operations console (`apps/web`)

## Environment

Copy `.env.example` to `.env` and adjust if needed. Compose uses the same variable names. Do not commit `.env`.

The API reads:

- `DATABASE_URL` — SQLAlchemy URL (asyncpg driver added automatically when missing)
- `FORGEFLOW_ENVIRONMENT`, `FORGEFLOW_LOG_LEVEL`, `FORGEFLOW_LOG_JSON`, `FORGEFLOW_API_PREFIX`
- `LLM_PROVIDER` — `openai`, `ollama`, or `mock` (Compose and `.env.example` default to `mock` so first boot needs no model server)
- `LLM_MODEL`, `LLM_API_BASE`, `LLM_API_KEY`, `LLM_TEMPERATURE`, `LLM_TIMEOUT_SECONDS`, `LLM_MAX_RETRIES`
- `FORGEFLOW_AS_OF` — investigation clock for the synthetic plant
- `MCP_TOOL_TIMEOUT_SECONDS`
- `CHECKPOINT_BACKEND` — `postgres` (Compose / `.env.example`) or `memory` (pytest)
- `FORGEFLOW_AUTH_SECRET` — HMAC secret for API bearer tokens
- `FORGEFLOW_CORS_ORIGINS` — CSV of browser origins for local Vite and the nginx console
- `FORGEFLOW_OTEL_ENABLED` — OpenTelemetry metrics (default true)

Default Compose credentials (`forgeflow` / `forgeflow`) and demo logins (`engineer` / `engineer-dev`, `manager` / `manager-dev`) are local-only.

## One-command core stack

```bash
docker compose up --build
```

This starts:

| Service | Port | Role |
| --- | --- | --- |
| `postgres` | 5432 | PostgreSQL 16 with pgvector |
| `api` | 8000 | FastAPI; runs `alembic upgrade head` on start |
| `web` | 3000 | nginx-hosted React console; proxies `/api` to `api` |
| `prometheus` | 9090 | Scrapes `api:8000/metrics` |
| `grafana` | 3001 | Provisioned ForgeFlow operations dashboard |

Verify:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/metrics
docker compose exec api python -m forgeflow.domain.seed --reset
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login -H "Content-Type: application/json" -d "{\"username\":\"engineer\",\"password\":\"engineer-dev\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
curl http://localhost:8000/api/v1/equipment/CNC-042 -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8000/api/v1/investigations -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d "{\"request\":\"Investigate overheating on CNC-042\"}"
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
python -m forgeflow.domain.seed --reset
uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

`DATABASE_URL` should point at `localhost` in this mode, which is the `.env.example` default.

## Operations console

After the API is running:

```powershell
cd apps/web
npm ci
npm run dev
```

Vite is at [http://localhost:5173](http://localhost:5173) and proxies `/api` to `http://127.0.0.1:8000`. Compose already exposes the production build at [http://localhost:3000](http://localhost:3000).

Sign in as `engineer` / `engineer-dev`, submit `Investigate overheating on CNC-042`, then sign in as `manager` / `manager-dev` to approve the work order.

Frontend checks:

```powershell
cd apps/web
npm run lint
npm test
npm run build
```

## Quality checks

```bash
ruff check forgeflow apps tests evals
ruff format --check forgeflow apps tests evals
mypy forgeflow apps evals
pytest
python -m evals
```

`tests/integration` talks to PostgreSQL when it is reachable and skips otherwise. Seeded CNC-042 assertions run in unit tests without a database. `python -m evals` writes `evals/reports/latest.json` and `latest.md` from a live mock run; see [evaluation.md](evaluation.md).

## Seed data

```bash
python -m forgeflow.domain.seed --reset
```

`--reset` deletes existing industrial rows, then inserts the synthetic plant and re-ingests fictional manuals into pgvector. The snapshot clock is `FORGEFLOW_AS_OF` when set (the Compose default), otherwise the process clock.

## Migrations

```bash
alembic upgrade head
alembic revision -m "describe the change"
```

Do not put credentials in `alembic.ini`. The env script reads `DATABASE_URL` through application settings.

## Optional services

Ollama is optional. Investigations work with `LLM_PROVIDER=mock` without a model server. Prometheus and Grafana start with Compose; see [observability.md](observability.md).
