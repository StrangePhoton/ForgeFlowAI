"""Security audit events are recorded without secrets."""

from fastapi.testclient import TestClient
from tests.conftest import auth_headers


def test_failed_login_and_forbidden_are_audited(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/login",
        json={"username": "engineer", "password": "nope"},
    )
    client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
        headers=auth_headers("viewer"),
    )
    events = client.get("/api/v1/audit", headers=auth_headers("admin"))
    assert events.status_code == 200
    types = {item["event_type"] for item in events.json()}
    assert "login_failure" in types
    assert "authorization_denied" in types
    blob = str(events.json())
    assert "engineer-dev" not in blob
    assert "nope" not in blob


def test_viewer_can_read_audit(client: TestClient) -> None:
    response = client.get("/api/v1/audit", headers=auth_headers("viewer"))
    assert response.status_code == 200
