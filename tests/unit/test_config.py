"""Configuration loading tests."""

import pytest
from forgeflow.config import Settings, get_settings
from pydantic import ValidationError


def test_async_database_url_adds_asyncpg_driver() -> None:
    settings = Settings.model_validate(
        {"database_url": "postgresql://forgeflow:secret@localhost:5432/forgeflow"}
    )
    assert settings.async_database_url.startswith("postgresql+asyncpg://")
    assert "secret" in settings.database_url


def test_async_database_url_keeps_existing_driver() -> None:
    url = "postgresql+asyncpg://forgeflow:secret@localhost:5432/forgeflow"
    settings = Settings.model_validate({"database_url": url})
    assert settings.async_database_url == url


def test_invalid_log_level_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://forgeflow:x@localhost:5432/forgeflow")
    monkeypatch.setenv("FORGEFLOW_LOG_LEVEL", "VERBOSE")
    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        Settings()


def test_api_prefix_normalized() -> None:
    settings = Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://forgeflow:x@localhost:5432/forgeflow",
            "api_prefix": "api/v1/",
        }
    )
    assert settings.api_prefix == "/api/v1"
