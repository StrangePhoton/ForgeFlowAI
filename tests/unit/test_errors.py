"""Application error mapping tests."""

from fastapi.testclient import TestClient
from forgeflow.errors import ForgeFlowError


def test_forgeflow_error_returns_json_envelope(client: TestClient) -> None:
    async def boom() -> None:
        raise ForgeFlowError("nope", code="test_error", status_code=409)

    client.app.add_api_route("/api/v1/_boom", boom, methods=["GET"])
    response = client.get("/api/v1/_boom")
    assert response.status_code == 409
    assert response.json() == {"error": {"code": "test_error", "message": "nope"}}


def test_unknown_route_returns_json_error(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"]["code"] == "http_error"
