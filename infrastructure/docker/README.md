# Docker

Container build files for ForgeFlow processes.

- `api/Dockerfile` — FastAPI image used by Compose and CI. The container starts with `python -m forgeflow.api.entrypoint` (migrate, then uvicorn) so Windows checkout line endings cannot break a shell shebang. The image copies `forgeflow`, `apps`, `evals`, and `sample_data` so hatch can build the wheel inside the container.

Prometheus scrape config lives in `infrastructure/prometheus/`. Grafana provisioning and the operations dashboard live in `infrastructure/grafana/`.
