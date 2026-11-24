"""HTTP authentication. Health stays public; industrial routes require a bearer token."""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader
from tests.conftest import auth_headers


def test_health_and_ready_are_public(anonymous_client: TestClient) -> None:
    health = anonymous_client.get("/api/v1/health")
    assert health.status_code == 200
    anonymous_client.app.state.database.ping = AsyncMock(return_value=None)
    ready = anonymous_client.get("/api/v1/ready")
    assert ready.status_code == 200


def test_equipment_without_token_is_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/api/v1/equipment")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_login_issues_token_and_me(anonymous_client: TestClient) -> None:
    login = anonymous_client.post(
        "/api/v1/auth/login",
        json={"username": "engineer", "password": "engineer-dev"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = anonymous_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "engineer"
    assert body["role"] == "engineer"
    assert "investigations:create" in body["permissions"]


def test_login_rejects_bad_password(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/api/v1/auth/login",
        json={"username": "engineer", "password": "wrong"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "unauthenticated"


def test_invalid_token_is_401(anonymous_client: TestClient) -> None:
    response = anonymous_client.get(
        "/api/v1/equipment",
        headers={"Authorization": "Bearer not-a-token"},
    )
    assert response.status_code == 401


def test_viewer_can_read_equipment(anonymous_client: TestClient) -> None:
    fake = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    anonymous_client.app.dependency_overrides[get_industrial_service] = lambda: fake
    listed = anonymous_client.get("/api/v1/equipment", headers=auth_headers("viewer"))
    assert listed.status_code == 200
