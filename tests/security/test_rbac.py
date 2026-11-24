"""Role checks live in application code. The model is not asked for permission."""

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader
from tests.conftest import auth_headers


def _install_fake(client: TestClient) -> InMemoryIndustrialReader:
    fake = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    client.app.dependency_overrides[get_industrial_service] = lambda: fake
    return fake


def test_viewer_cannot_create_investigation(client: TestClient) -> None:
    _install_fake(client)
    response = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
        headers=auth_headers("viewer"),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "forbidden"


def test_engineer_cannot_approve(client: TestClient) -> None:
    _install_fake(client)
    started = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    assert started.status_code == 200
    investigation_id = started.json()["investigation_id"]
    denied = client.post(
        f"/api/v1/approvals/{investigation_id}/approve",
        json={"decision": "approve"},
    )
    assert denied.status_code == 403
    assert started.json()["work_order"] is None


def test_manager_can_approve_after_engineer_investigation(client: TestClient) -> None:
    fake = _install_fake(client)
    started = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    investigation_id = started.json()["investigation_id"]
    approved = client.post(
        f"/api/v1/approvals/{investigation_id}/approve",
        json={"decision": "approve"},
        headers=auth_headers("maintenance_manager"),
    )
    assert approved.status_code == 200
    assert approved.json()["work_order"] is not None
    assert len(fake._created_work_orders) == 1
