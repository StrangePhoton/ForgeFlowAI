# ForgeFlow AI

Production-oriented industrial agentic AI platform. An engineer can submit an operational request; the system plans an investigation, gathers equipment telemetry, alarms, and maintenance history through MCP tools, and produces an evidence-backed root-cause report.

**Current status: Milestone 3 (investigation workflow).** MCP tools and a LangGraph investigation run against the synthetic plant. RAG, human approval, authentication, and the web console are not implemented yet.

## Problem

Industrial investigations mix noisy operational data, technical manuals, and write actions that must not run unchecked. A chatbot wrapper around an LLM cannot own that workflow: authorization, tool execution, evidence, approval, and audit have to be software systems, with the model used only where judgment is actually required.

## What works today

- FastAPI application with versioned health, readiness, equipment history, and investigation endpoints
- PostgreSQL 16 with pgvector enabled and industrial tables for equipment, telemetry, alarms, maintenance, and work orders
- Deterministic synthetic seed for five fictional machines, including CNC-042
- MCP tools `get_equipment`, `get_sensor_history`, `get_alarm_history`, and `get_maintenance_history`
- LangGraph investigation: request → plan → equipment → telemetry → alarms → maintenance → evidence → report
- LLM provider abstraction for OpenAI, Ollama, and an in-process mock (tests never call a paid API)
- Environment-based configuration
- JSON structured logging with secret redaction
- Docker Compose for `postgres` and `api`
- pytest, ruff, mypy, and a GitHub Actions workflow

## What does not work yet

- RAG / document retrieval
- Human approval
- Authentication and RBAC
- React operations console
- Evaluation harness
- OpenTelemetry / Prometheus / Grafana

See [docs/architecture.md](docs/architecture.md) for the target design and [docs/local-development.md](docs/local-development.md) for setup.

## Architecture (target)

```mermaid
flowchart LR
    User[Operator] --> Web[Web console]
    Web --> API[FastAPI]
    API --> Graph[LangGraph]
    Graph --> MCP[MCP tools]
    MCP --> DB[(PostgreSQL + pgvector)]
    Graph --> RAG[Retrieval]
    RAG --> DB
    Graph --> HITL[Approval queue]
    HITL --> User
```

Milestone 3 implements the investigation path through MCP tools:

```mermaid
flowchart LR
    Client[HTTP client] --> API[FastAPI /api/v1]
    API --> Graph[LangGraph investigation]
    Graph --> EqMCP[Equipment MCP]
    Graph --> MaintMCP[Maintenance MCP]
    EqMCP --> Reader[IndustrialQueryService]
    MaintMCP --> Reader
    Reader --> DB[(PostgreSQL)]
```

## Technology stack

| Area | Choice |
| --- | --- |
| API | Python 3.12+, FastAPI, Pydantic v2 |
| Data | PostgreSQL 16, pgvector, SQLAlchemy 2, Alembic |
| Tools | MCP (`mcp` SDK) wrapping industrial read queries |
| Agent | LangGraph explicit state graph |
| LLM | OpenAI, Ollama, or in-process mock |
| Packaging | Docker Compose |
| Quality | pytest, ruff, mypy, GitHub Actions |

## Quick start

Requirements: Docker Desktop (or another Compose-compatible Docker engine).

```bash
git clone <repository-url>
cd forgeflow-ai
cp .env.example .env
docker compose up --build
docker compose exec api python -m forgeflow.domain.seed --reset
```

Then:

```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/ready
curl http://localhost:8000/api/v1/equipment/CNC-042
curl -X POST http://localhost:8000/api/v1/investigations \
  -H "Content-Type: application/json" \
  -d "{\"request\":\"Investigate overheating on CNC-042\"}"
```

The investigation endpoint uses `LLM_PROVIDER` from `.env`. The Compose default is Ollama; set `LLM_PROVIDER=mock` to run without a model server. Tests always use the mock provider.

Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Default local credentials in `.env.example` are for development only.

## Demo scenario

CNC-042 (ForgeMach FX-400) has a planted last-30-day pattern:

- rising temperature
- declining coolant flow
- nine `TEMP_HIGH` alarms
- overdue cooling-system inspection
- no open work order for cooling

An investigation for CNC-042 should produce FACT / INFERENCE / RECOMMENDATION findings that cite those signals. Peer assets (PUMP-AX200, CONVEYOR-B17, PRESS-HYD-03, COMPRESSOR-C09) do not share that pattern.

## Local checks (without Docker)

Python 3.12+ is required. On Windows, create a venv and install extras:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
ruff check forgeflow apps tests
ruff format --check forgeflow apps tests
mypy forgeflow apps
pytest
```

Integration tests skip automatically when PostgreSQL is not reachable. Against a migrated database:

```powershell
alembic upgrade head
python -m forgeflow.domain.seed --reset
pytest -m integration
```

## License

MIT. See [LICENSE](LICENSE).
