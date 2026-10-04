"""HTTP equipment routes with an in-memory fake service."""

from datetime import timedelta

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import PlantSnapshot, generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader

SEED_NOW = DEMO_CLOCK


def _install_fake(client: TestClient) -> PlantSnapshot:
    snapshot = generate_plant(now=SEED_NOW)
    fake = InMemoryIndustrialReader(snapshot)
    client.app.dependency_overrides[get_industrial_service] = lambda: fake
    return snapshot


def test_list_and_get_cnc_042(client: TestClient) -> None:
    _install_fake(client)
    listed = client.get("/api/v1/equipment")
    assert listed.status_code == 200
    codes = {item["code"] for item in listed.json()}
    assert "CNC-042" in codes
    detail = client.get("/api/v1/equipment/CNC-042")
    assert detail.status_code == 200
    body = detail.json()
    assert body["code"] == "CNC-042"
    assert body["model"] == "FX-400"


def test_unknown_equipment_returns_not_found(client: TestClient) -> None:
    _install_fake(client)
    response = client.get("/api/v1/equipment/UNKNOWN-1")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_cnc_history_endpoints(client: TestClient) -> None:
    _install_fake(client)
    start = (SEED_NOW - timedelta(days=30)).isoformat()
    end = SEED_NOW.isoformat()
    telemetry = client.get(
        "/api/v1/equipment/CNC-042/sensor-history",
        params={"start": start, "end": end},
    )
    alarms = client.get(
        "/api/v1/equipment/CNC-042/alarm-history",
        params={"start": start, "end": end},
    )
    maintenance = client.get("/api/v1/equipment/CNC-042/maintenance-history")
    work_orders = client.get("/api/v1/equipment/CNC-042/work-orders")
    assert telemetry.status_code == 200
    assert alarms.status_code == 200
    assert maintenance.status_code == 200
    assert work_orders.status_code == 200
    assert len(telemetry.json()) > 100
    assert any(item["code"] == "TEMP_HIGH" for item in alarms.json())
    assert any(item["title"] == "Cooling system inspection" for item in maintenance.json())
    assert work_orders.json() == []
