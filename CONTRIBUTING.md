# Contributing

ForgeFlow AI is developed in vertical slices. Milestone 10 is the current baseline: keep the repository bootable with `docker compose up`, a passing test suite, CNC-042 investigations, the operations console, `python -m evals`, `/metrics` populated from real operations, and docs that match what actually runs.

Report security issues using [SECURITY.md](SECURITY.md), not a public bug ticket. Recapture console images using [docs/screenshots/README.md](docs/screenshots/README.md).

## Development setup

1. Install Python 3.12 or later.
2. Create a virtual environment and install the package with dev extras.
3. Copy `.env.example` to `.env` for local overrides.
4. Start PostgreSQL with Docker Compose, or run unit tests without a database.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
docker compose up postgres -d
alembic upgrade head
python -m forgeflow.domain.seed --reset
pytest
```

## Checks

Run the same checks CI runs:

```powershell
ruff check forgeflow apps tests evals
ruff format --check forgeflow apps tests evals
mypy forgeflow apps evals
pytest
python -m evals
cd apps/web
npm ci
npm run lint
npm test
npm run build
```

Do not add paid LLM or embedding API calls to the default test suite. External model APIs must remain mockable. Retrieval uses hashed embeddings.

## Project conventions

- Prefer deterministic application code over LLM decisions.
- Put imports at the top of Python modules, not inside functions.
- Do not commit `.env`, secrets, proprietary industrial data, or hand-written eval report numbers.
- Document only behavior that is implemented. Mark unfinished work as such.
- New domain tables belong in Alembic migrations, not ad-hoc SQL in application code.

## Pull requests

- Keep pull requests small. The planned M0–M10 slices are complete; do not reintroduce unfinished-milestone placeholders.
- Include tests for API, database, and security-sensitive behavior.
- Update README and docs when behavior changes.
