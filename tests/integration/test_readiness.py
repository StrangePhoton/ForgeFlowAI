"""Readiness checks against a real PostgreSQL instance when one is available."""

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.integration


def test_ready_succeeds_against_live_database(client: TestClient, require_postgres: None) -> None:
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"]["database"] == "ok"
