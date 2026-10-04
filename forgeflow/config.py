"""Application configuration loaded from environment variables."""

from datetime import datetime
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for the API process.

    Secrets belong in the environment (or a local `.env` file that is not committed).
    Provider-specific LLM fields select OpenAI, Ollama, or the in-process mock.
    Azure OpenAI can reuse the OpenAI adapter with a different base URL later.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        populate_by_name=True,
    )

    app_name: str = "forgeflow-api"
    environment: str = Field(default="development", validation_alias="FORGEFLOW_ENVIRONMENT")
    log_level: str = Field(default="INFO", validation_alias="FORGEFLOW_LOG_LEVEL")
    log_json: bool = Field(default=True, validation_alias="FORGEFLOW_LOG_JSON")
    api_prefix: str = Field(default="/api/v1", validation_alias="FORGEFLOW_API_PREFIX")

    database_url: str = Field(
        default="postgresql+asyncpg://forgeflow:forgeflow@127.0.0.1:5432/forgeflow",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=5, ge=1, le=50)
    database_max_overflow: int = Field(default=10, ge=0, le=50)
    database_pool_timeout_seconds: int = Field(default=30, ge=1, le=120)
    database_ping_timeout_seconds: float = Field(default=3.0, ge=0.5, le=30.0)
    database_echo: bool = False

    llm_provider: Literal["openai", "ollama", "mock"] = Field(
        default="ollama", validation_alias="LLM_PROVIDER"
    )
    llm_model: str = Field(default="llama3.1", validation_alias="LLM_MODEL")
    llm_api_base: str | None = Field(default=None, validation_alias="LLM_API_BASE")
    llm_api_key: str | None = Field(default=None, validation_alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0, validation_alias="LLM_TEMPERATURE")
    llm_timeout_seconds: float = Field(default=60.0, ge=1.0, validation_alias="LLM_TIMEOUT_SECONDS")
    llm_max_retries: int = Field(default=3, ge=0, le=8, validation_alias="LLM_MAX_RETRIES")

    mcp_tool_timeout_seconds: float = Field(
        default=15.0, ge=0.1, le=120.0, validation_alias="MCP_TOOL_TIMEOUT_SECONDS"
    )
    investigation_as_of: datetime | None = Field(default=None, validation_alias="FORGEFLOW_AS_OF")

    @field_validator("log_level")
    @classmethod
    def normalize_log_level(cls, value: str) -> str:
        normalized = value.upper()
        allowed = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"}
        if normalized not in allowed:
            msg = f"log_level must be one of {sorted(allowed)}"
            raise ValueError(msg)
        return normalized

    @field_validator("api_prefix")
    @classmethod
    def normalize_api_prefix(cls, value: str) -> str:
        prefix = value.rstrip("/")
        if not prefix.startswith("/"):
            prefix = f"/{prefix}"
        return prefix

    @property
    def async_database_url(self) -> str:
        """Return a SQLAlchemy asyncpg URL regardless of the configured scheme."""
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return process-wide settings. Clear the cache in tests after env changes."""
    return Settings()
