PYTHON ?= python
COMPOSE ?= docker compose

.PHONY: help install lint format typecheck test check up down logs migrate

help:
	@echo "install     Install the package with dev extras"
	@echo "lint        Run ruff"
	@echo "format      Format with ruff"
	@echo "typecheck   Run mypy"
	@echo "test        Run pytest"
	@echo "check       lint + format check + mypy + pytest"
	@echo "up          Start core Compose services"
	@echo "down        Stop Compose services"
	@echo "logs        Follow API logs"
	@echo "migrate     Apply Alembic migrations"

install:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	ruff check forgeflow apps tests

format:
	ruff format forgeflow apps tests

typecheck:
	mypy forgeflow apps

test:
	pytest -q

check: lint
	ruff format --check forgeflow apps tests
	$(MAKE) typecheck
	$(MAKE) test

up:
	$(COMPOSE) up --build -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f api

migrate:
	alembic upgrade head
