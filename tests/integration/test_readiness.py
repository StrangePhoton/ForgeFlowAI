"""Readiness checks against a real PostgreSQL instance when one is available."""

from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from forgeflow.config import get_settings
from forgeflow.db.session import Database

pytestmark = pytest.mark.integration


async def _postgres_reachable() -> bool:
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
    if not await _postgres_reachable():
        pytest.skip("PostgreSQL is not reachable on DATABASE_URL")
    yield


def test_ready_succeeds_against_live_database(client: TestClient, require_postgres: None) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"] == "ok"
