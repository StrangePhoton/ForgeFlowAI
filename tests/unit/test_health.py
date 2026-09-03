"""Tests for liveness and readiness endpoints."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from forgeflow import __version__


def test_health_returns_healthy(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "forgeflow-api"
    assert body["version"] == __version__
    assert body["environment"] == "test"


def test_health_does_not_require_database(client: TestClient) -> None:
    client.app.state.database.ping = AsyncMock(side_effect=OSError("unreachable"))
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    client.app.state.database.ping.assert_not_called()


def test_health_propagates_request_id(client: TestClient) -> None:
    response = client.get("/api/v1/health", headers={"X-Request-ID": "req-123"})
    assert response.headers["X-Request-ID"] == "req-123"


def test_ready_returns_ready_when_database_pings(client: TestClient) -> None:
    client.app.state.database.ping = AsyncMock(return_value=None)
    response = client.get("/api/v1/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"database": "ok"}}


def test_ready_returns_503_when_database_unavailable(client: TestClient) -> None:
    client.app.state.database.ping = AsyncMock(side_effect=OSError("connection refused"))
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"]["database"] == "unavailable"
    assert body["error"]["code"] == "dependency_unavailable"
    assert "password" not in response.text.lower()


def test_ready_returns_503_for_driver_errors(client: TestClient) -> None:
    client.app.state.database.ping = AsyncMock(
        side_effect=RuntimeError("connection was closed in the middle of operation")
    )
    response = client.get("/api/v1/ready")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "dependency_unavailable"
