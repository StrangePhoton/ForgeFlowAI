# Contributing

ForgeFlow AI is developed in vertical slices. Milestone 1 is the current baseline: keep the repository bootable with `docker compose up`, a passing test suite, and a seedable CNC-042 plant.

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
ruff check forgeflow apps tests
ruff format --check forgeflow apps tests
mypy forgeflow apps
pytest
```

Do not add paid LLM calls to the default test suite. External model APIs must remain mockable.

## Project conventions

- Prefer deterministic application code over LLM decisions.
- Put imports at the top of Python modules, not inside functions.
- Do not commit `.env`, secrets, or proprietary industrial data.
- Document only behavior that is implemented. Mark unfinished work as such.
- New domain tables belong in Alembic migrations, not ad-hoc SQL in application code.

## Pull requests

- Keep changes scoped to the current milestone unless a tiny abstraction is required to avoid immediate debt.
- Include tests for API, database, and security-sensitive behavior.
- Update README and docs when behavior changes.
