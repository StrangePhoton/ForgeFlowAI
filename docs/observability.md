# Observability

ForgeFlow records real HTTP, investigation, tool, retrieval, and LLM operations through OpenTelemetry. The Prometheus exporter serves those instruments at `GET /metrics`. Grafana is optional local UI, not a source of fake numbers.

## Endpoints

| URL | Meaning |
| --- | --- |
| [http://localhost:8000/metrics](http://localhost:8000/metrics) | Prometheus text exposition |
| [http://localhost:9090](http://localhost:9090) | Prometheus UI (Compose) |
| [http://localhost:3001](http://localhost:3001) | Grafana (Compose). Anonymous viewer; admin/admin locally |

`/metrics` is public so a local scraper can collect. Scrapes are excluded from both ForgeFlow HTTP instruments and FastAPI's built-in OpenTelemetry so the endpoint does not record itself. Do not expose it on an untrusted network without an access control layer.

## Instruments

| Metric | When it moves |
| --- | --- |
| `forgeflow_http_requests_total` / `forgeflow_http_duration_seconds` | Each API request except `/metrics` (`http_route` is the prefixed template, e.g. `/api/v1/health`) |
| `forgeflow_agent_runs_total` / `forgeflow_agent_duration_seconds` | Each investigation `run` or `resume` (`outcome` is status or `error`) |
| `forgeflow_tool_calls_total` / `forgeflow_tool_duration_seconds` | Each MCP tool invocation |
| `forgeflow_retrieval_requests_total` / `forgeflow_retrieval_duration_seconds` | `search_documentation` |
| `forgeflow_llm_requests_total` / `forgeflow_llm_duration_seconds` | Each structured LLM completion |
| `forgeflow_llm_tokens_total` | Prompt/completion tokens when the OpenAI adapter reports usage |
| `forgeflow_approvals_total` | Investigation first reaches `awaiting_approval` |

Traces use the OpenTelemetry tracer (`investigation.run`, `investigation.resume`). The default local stack exports metrics to Prometheus; spans stay in-process unless you attach another exporter later.

Disable with `FORGEFLOW_OTEL_ENABLED=false`.

## Local stack

```bash
docker compose up --build
```

After an investigation, Prometheus should list `forgeflow_*` series and Grafana should show the **ForgeFlow operations** dashboard.
