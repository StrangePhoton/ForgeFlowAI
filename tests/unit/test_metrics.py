"""Prometheus metrics come from real HTTP, tool, and investigation operations."""

from fastapi.testclient import TestClient
from forgeflow.api.deps import get_industrial_service
from forgeflow.domain.seed.constants import DEMO_CLOCK
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.services.snapshot import InMemoryIndustrialReader


def test_metrics_endpoint_is_public(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]


def test_health_request_appears_in_metrics(anonymous_client: TestClient) -> None:
    health = anonymous_client.get("/api/v1/health")
    assert health.status_code == 200
    body = anonymous_client.get("/metrics").text
    assert "forgeflow_http_requests_total" in body
    assert 'http_route="/api/v1/health"' in body
    assert "http_method" in body
    assert 'http_route="/metrics"' not in body
    assert 'le="0.005"' in body


def test_investigation_records_agent_tool_and_approval_metrics(client: TestClient) -> None:
    fake = InMemoryIndustrialReader(generate_plant(now=DEMO_CLOCK))
    client.app.dependency_overrides[get_industrial_service] = lambda: fake
    started = client.post(
        "/api/v1/investigations",
        json={"request": "Investigate overheating on CNC-042"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "awaiting_approval"
    body = client.get("/metrics").text
    assert "forgeflow_agent_runs_total" in body
    assert "awaiting_approval" in body
    assert "forgeflow_tool_calls_total" in body
    assert "get_sensor_history" in body
    assert "forgeflow_approvals_total" in body
    assert "forgeflow_llm_requests_total" in body
    assert "forgeflow_retrieval_requests_total" in body
    assert 'http_route="/api/v1/investigations"' in body
