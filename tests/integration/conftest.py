"""Shared PostgreSQL fixtures for integration tests."""

import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import PlantSnapshot, generate_plant
from forgeflow.domain.seed.persist import persist_plant
from forgeflow.retrieval.ingestion import ingest_manuals

SEED_NOW = DEMO_CLOCK


async def postgres_reachable() -> bool:
    database = Database(get_settings())
    reachable = False
    try:
        await database.ping()
        reachable = True
    except Exception:
        reachable = False
    try:
        await database.dispose()
    except Exception:
        reachable = False
    return reachable


@pytest.fixture
async def require_postgres() -> AsyncIterator[None]:
    if not await postgres_reachable():
        pytest.skip("PostgreSQL is not reachable on DATABASE_URL")
    yield


def apply_migrations() -> None:
    scripts_dir = Path(sys.executable).parent
    alembic = scripts_dir / ("alembic.exe" if sys.platform == "win32" else "alembic")
    subprocess.run([str(alembic), "upgrade", "head"], check=True)


@pytest.fixture
async def seeded_plant(require_postgres: None) -> AsyncIterator[PlantSnapshot]:
    apply_migrations()
    snapshot = generate_plant(now=SEED_NOW)
    database = Database(get_settings())
    try:
        async with database.session_factory() as session:
            await persist_plant(session, snapshot, reset=True)
            await ingest_manuals(session, reset=True)
            await session.commit()
        yield snapshot
    finally:
        await database.dispose()
