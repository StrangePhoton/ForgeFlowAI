"""HTTP investigation and approval endpoints using the in-memory plant."""

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import CNC_CODE, DEMO_CLOCK, TEMP_HIGH_CODE
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader


def _install_fake(client: TestClient) -> InMemoryIndustrialReader:
    fake = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    client.app.dependency_overrides[get_industrial_service] = lambda: fake
    return fake


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
    assert body["status"] == "awaiting_approval"
    assert body["work_order"] is None
    findings = " ".join(item["statement"] for item in body["report"]["findings"])
    assert TEMP_HIGH_CODE in findings
    assert "cnc-042-cooling.md" in findings
    kinds = {item["kind"] for item in body["report"]["findings"]}
    assert kinds >= {"FACT", "INFERENCE", "RECOMMENDATION"}
    sources = {item["source"] for item in body["report"]["findings"]}
    assert "search_documentation" in sources


def test_investigation_rejects_empty_request(client: TestClient) -> None:
    _install_fake(client)
    response = client.post("/api/v1/investigations", json={"request": ""})
    assert response.status_code == 422


def test_approve_creates_one_work_order(client: TestClient) -> None:
    fake = _install_fake(client)
    started = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    investigation_id = started.json()["investigation_id"]
    pending = client.get("/api/v1/approvals")
    assert pending.status_code == 200
    assert any(item["investigation_id"] == investigation_id for item in pending.json())
    approved = client.post(
        f"/api/v1/approvals/{investigation_id}/approve",
        json={"decision": "approve"},
    )
    assert approved.status_code == 200
    body = approved.json()
    assert body["status"] == "completed"
    assert body["work_order"] is not None
    assert body["work_order"]["title"]
    listed = client.get(f"/api/v1/equipment/{CNC_CODE}/work-orders")
    created = [
        item
        for item in listed.json()
        if item.get("idempotency_key") == f"investigation:{investigation_id}:create_work_order"
    ]
    assert len(created) == 1
    replay = client.post(
        f"/api/v1/approvals/{investigation_id}/approve",
        json={"decision": "approve"},
    )
    assert replay.status_code == 404
    assert len(fake._created_work_orders) == 1


def test_reject_creates_no_work_order(client: TestClient) -> None:
    fake = _install_fake(client)
    started = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    investigation_id = started.json()["investigation_id"]
    rejected = client.post(
        f"/api/v1/approvals/{investigation_id}/reject",
        json={"decision": "reject", "reason": "Hold for next shift"},
    )
    assert rejected.status_code == 200
    body = rejected.json()
    assert body["status"] == "rejected"
    assert body["work_order"] is None
    assert fake._created_work_orders == []
