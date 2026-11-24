"""Browser origins must be able to call the API during local Vite development."""

from fastapi.testclient import TestClient


def test_cors_preflight_allows_vite_origin(anonymous_client: TestClient) -> None:
    response = anonymous_client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code in {200, 204}
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "authorization" in (response.headers.get("access-control-allow-headers") or "").lower()


def test_cors_get_exposes_origin(anonymous_client: TestClient) -> None:
    response = anonymous_client.get(
        "/api/v1/health",
        headers={"Origin": "http://127.0.0.1:3000"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
