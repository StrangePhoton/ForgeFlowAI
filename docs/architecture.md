# Architecture

ForgeFlow AI is a modular monolith. One Python package (`forgeflow`) owns domain logic, agent orchestration, retrieval, and security. Process entrypoints live under `apps/`. MCP servers may run as separate processes later, but they share the same package and database rather than becoming a microservice mesh.

## Milestone 1 scope

Implemented now:

- FastAPI application factory with `/api/v1/health` and `/api/v1/ready`
- Equipment registry and history APIs under `/api/v1/equipment`
- Pydantic Settings loaded from the environment
- Async SQLAlchemy engine and session factory
- Alembic migrations, including `CREATE EXTENSION vector` and industrial tables
- Deterministic synthetic seed (CNC-042 overheating scenario)
- Structured JSON logging and request IDs
- Docker Compose services: `postgres`, `api`

Not implemented: agent graph, MCP, RAG, authn/z, UI, evals, OpenTelemetry.

## Target runtime

```mermaid
flowchart TB
    subgraph clients [Clients]
        Web[React operations console]
        APIClient[HTTP / OpenAPI clients]
    end

    subgraph apiProcess [API process]
        HTTP[FastAPI routers]
        Auth[RBAC]
        Graph[LangGraph investigation]
        Providers[LLM provider adapter]
    end

    subgraph tools [Tool boundary]
        EqMCP[Equipment MCP]
        MaintMCP[Maintenance MCP]
        DocMCP[Documentation MCP]
    end

    subgraph data [Data]
        PG[(PostgreSQL)]
        Vec[pgvector chunks]
    end

    Web --> HTTP
    APIClient --> HTTP
    HTTP --> Auth
    Auth --> Graph
    Graph --> Providers
    Graph --> EqMCP
    Graph --> MaintMCP
    Graph --> DocMCP
    EqMCP --> PG
    MaintMCP --> PG
    DocMCP --> Vec
    Graph --> PG
```

## Design rules

1. **The LLM is not a security boundary.** Authorization, write-action gating, and schema validation happen in application code.
2. **External content is untrusted.** Manuals, telemetry labels, and tool payloads cannot override system instructions.
3. **Write actions require deterministic policy plus human approval.** The graph interrupts and resumes from PostgreSQL-backed checkpoints.
4. **Critical model outputs are Pydantic models.** Plans, evidence, risk, and reports are not parsed from free-form prose.
5. **Agent reasoning and tool execution stay separated.** The graph decides; MCP tools execute with explicit schemas and authz checks.
6. **Failures are visible.** Insufficient evidence is a first-class outcome, not a confident hallucination.

## Package map

| Path | Responsibility | First milestone |
| --- | --- | --- |
| `apps/api` | ASGI entrypoint | 0 |
| `forgeflow/api` | HTTP app, routes, error envelope | 0 |
| `forgeflow/config.py` | Settings | 0 |
| `forgeflow/db` | Engine, session, Alembic | 0 |
| `forgeflow/observability` | Logging (metrics in M9) | 0 |
| `forgeflow/domain` | Equipment, telemetry, work orders | 1 |
| `forgeflow/services` | Read queries for industrial data | 1 |
| `forgeflow/mcp` | MCP servers and tool schemas | 2 |
| `forgeflow/agent` | LangGraph, providers, prompts | 3 |
| `forgeflow/retrieval` | Ingestion, embeddings, search | 4 |
| `forgeflow/security` | Authn, RBAC, tool authz | 6 |
| `apps/web` | Operations console | 7 |
| `evals` | Synthetic evaluation runner | 8 |

## HTTP API

Versioned under `/api/v1`. Milestone 1 exposes:

| Method | Path | Meaning |
| --- | --- | --- |
| GET | `/api/v1/health` | Process liveness; no database access |
| GET | `/api/v1/ready` | Readiness; `SELECT 1` against PostgreSQL |
| GET | `/api/v1/equipment` | List seeded assets |
| GET | `/api/v1/equipment/{code}` | Equipment by code or UUID |
| GET | `/api/v1/equipment/{code}/sensor-history` | Telemetry; default last 30 days |
| GET | `/api/v1/equipment/{code}/alarm-history` | Alarms; default last 30 days |
| GET | `/api/v1/equipment/{code}/maintenance-history` | Maintenance records |
| GET | `/api/v1/equipment/{code}/work-orders` | Work orders for the asset |
| GET | `/docs` | OpenAPI Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

Errors use `{ "error": { "code", "message", "details?" } }`.

## Persistence

PostgreSQL is the system of record for operational data, checkpoints, audit events, and embeddings. pgvector is enabled in the first migration. Milestone 1 adds `equipment`, `sensor_readings`, `alarms`, `maintenance_records`, and `work_orders`.

Synthetic catalogs live in `sample_data/`. Hourly telemetry is generated at seed time by `python -m forgeflow.domain.seed`.

## Configuration

Settings are loaded by `pydantic-settings`. `DATABASE_URL` may be `postgresql://` or `postgresql+asyncpg://`; the application normalizes to asyncpg. LLM provider fields are accepted now and unused until Milestone 3, so provider configuration does not scatter later.

See [local-development.md](local-development.md) and [adr/](adr/).
