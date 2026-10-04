# Docker

Container build files for ForgeFlow processes.

- `api/Dockerfile` — FastAPI image used by Compose and CI. The container starts with `python -m forgeflow.api.entrypoint` (migrate, then uvicorn) so Windows checkout line endings cannot break a shell shebang.

Prometheus and Grafana assets belong here in Milestone 9.
