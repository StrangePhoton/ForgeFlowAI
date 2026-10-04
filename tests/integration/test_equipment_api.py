"""Equipment APIs against a seeded PostgreSQL database."""

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import PlantSnapshot

pytestmark = pytest.mark.integration

SEED_NOW = DEMO_CLOCK


def test_cnc_042_round_trip(client: TestClient, seeded_plant: PlantSnapshot) -> None:
    start = (SEED_NOW - timedelta(days=30)).isoformat()
    end = SEED_NOW.isoformat()

    detail = client.get(f"/api/v1/equipment/{CNC_CODE}")
    assert detail.status_code == 200
    assert detail.json()["code"] == CNC_CODE
    assert detail.json()["model"] == "FX-400"

    telemetry = client.get(
        f"/api/v1/equipment/{CNC_CODE}/sensor-history",
        params={"start": start, "end": end, "limit": 2000},
    )
    alarms = client.get(
        f"/api/v1/equipment/{CNC_CODE}/alarm-history",
        params={"start": start, "end": end},
    )
    maintenance = client.get(f"/api/v1/equipment/{CNC_CODE}/maintenance-history")
    work_orders = client.get(f"/api/v1/equipment/{CNC_CODE}/work-orders")

    assert telemetry.status_code == 200
    assert alarms.status_code == 200
    assert maintenance.status_code == 200
    assert work_orders.status_code == 200

    readings = telemetry.json()
    assert len(readings) > 200
    assert any(row["coolant_flow"] is not None for row in readings)
    assert any(row["code"] == TEMP_HIGH_CODE for row in alarms.json())
    cooling = next(row for row in maintenance.json() if row["title"] == "Cooling system inspection")
    due = datetime.fromisoformat(cooling["next_due_at"].replace("Z", "+00:00"))
    assert due < SEED_NOW
    assert work_orders.json() == []
    assert seeded_plant.equipment_by_code(CNC_CODE).code == CNC_CODE


def test_unknown_equipment_against_database(
    client: TestClient, seeded_plant: PlantSnapshot
) -> None:
    response = client.get("/api/v1/equipment/NO-SUCH")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
