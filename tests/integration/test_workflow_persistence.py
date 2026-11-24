"""Investigations, approvals, audit, and login survive an API process restart."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from forgeflow.api.app import create_app
from forgeflow.config import get_settings
from forgeflow.domain.seed.generate import PlantSnapshot
from tests.conftest import auth_headers


@pytest.fixture
def durable_settings(
    monkeypatch: pytest.MonkeyPatch, test_environment: None
) -> Generator[None, None, None]:
    del test_environment
    monkeypatch.setenv("CHECKPOINT_BACKEND", "postgres")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.integration
def test_login_uses_seeded_users_table(durable_settings: None, seeded_plant: PlantSnapshot) -> None:
    del durable_settings, seeded_plant
    with TestClient(create_app()) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={"username": "engineer", "password": "engineer-dev"},
        )
        assert login.status_code == 200
        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["username"] == "engineer"


@pytest.mark.integration
def test_investigation_survives_api_restart(
    durable_settings: None, seeded_plant: PlantSnapshot
) -> None:
    del durable_settings, seeded_plant
    started_id: str
    with TestClient(create_app()) as first:
        first.headers.update(auth_headers("engineer"))
        started = first.post(
            "/api/v1/investigations",
            json={"request": "Investigate overheating on CNC-042"},
        )
        assert started.status_code == 200
        body = started.json()
        assert body["status"] == "awaiting_approval"
        findings = " ".join(item["statement"] for item in body["report"]["findings"])
        assert "cnc-042-cooling.md" in findings
        started_id = body["investigation_id"]

    with TestClient(create_app()) as restarted:
        listed = restarted.get("/api/v1/investigations", headers=auth_headers("engineer"))
        assert listed.status_code == 200
        ids = {item["investigation_id"] for item in listed.json()}
        assert started_id in ids
        pending = restarted.get("/api/v1/approvals", headers=auth_headers("maintenance_manager"))
        assert any(item["investigation_id"] == started_id for item in pending.json())
        approved = restarted.post(
            f"/api/v1/approvals/{started_id}/approve",
            json={"decision": "approve"},
            headers=auth_headers("maintenance_manager"),
        )
        assert approved.status_code == 200
        assert approved.json()["status"] == "completed"
        assert approved.json()["work_order"] is not None
        audit = restarted.get("/api/v1/audit", headers=auth_headers("admin"))
        types = {item["event_type"] for item in audit.json()}
        assert "investigation_started" in types
        assert "approval_decided" in types
        assert "work_order_created" in types
