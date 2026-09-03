"""Typed application errors used by the API and later agent/tool layers."""

from typing import Any


class ForgeFlowError(Exception):
    """Base error for expected ForgeFlow failures."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "internal_error",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class DependencyUnavailableError(ForgeFlowError):
    """A required runtime dependency (for example PostgreSQL) is unreachable."""

    def __init__(self, message: str = "A required dependency is unavailable") -> None:
        super().__init__(message, code="dependency_unavailable", status_code=503)
