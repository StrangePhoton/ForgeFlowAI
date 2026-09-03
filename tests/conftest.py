"""Shared pytest fixtures."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from forgeflow.api.app import create_app
from forgeflow.config import get_settings


@pytest.fixture(autouse=True)
def test_environment(monkeypatch: pytest.MonkeyPatch) -> Generator[None, None, None]:
    monkeypatch.setenv("FORGEFLOW_ENVIRONMENT", "test")
    monkeypatch.setenv("FORGEFLOW_LOG_JSON", "true")
    monkeypatch.setenv("FORGEFLOW_LOG_LEVEL", "INFO")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(test_environment: None) -> Generator[TestClient, None, None]:
    application = create_app()
    with TestClient(application) as test_client:
        yield test_client
