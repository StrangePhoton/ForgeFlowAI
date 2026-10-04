"""HTTP investigation endpoint using the in-memory plant and mock LLM."""

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _install_fake(client: TestClient) -> None:
    fake = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    client.app.dependency_overrides[get_industrial_service] = lambda: fake


def test_investigation_endpoint_cnc_042(client: TestClient) -> None:
    _install_fake(client)
    response = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["equipment_code"] == CNC_CODE
    assert body["report"]["evidence_sufficient"] is True
    findings = " ".join(item["statement"] for item in body["report"]["findings"])
    assert TEMP_HIGH_CODE in findings
    kinds = {item["kind"] for item in body["report"]["findings"]}
    assert kinds >= {"FACT", "INFERENCE", "RECOMMENDATION"}


def test_investigation_rejects_empty_request(client: TestClient) -> None:
    _install_fake(client)
    response = client.post("/api/v1/investigations", json={"request": ""})
    assert response.status_code == 422
