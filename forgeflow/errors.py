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


class NotFoundError(ForgeFlowError):
    """The requested domain object does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message, code="not_found", status_code=404)


class ToolValidationError(ForgeFlowError):
    """MCP tool arguments failed schema validation."""

    def __init__(
        self,
        message: str = "Tool arguments are invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, code="tool_validation_error", status_code=422, details=details)


class ToolTimeoutError(ForgeFlowError):
    """An MCP tool exceeded its execution timeout."""

    def __init__(self, message: str = "Tool execution timed out") -> None:
        super().__init__(message, code="tool_timeout", status_code=504)


class ToolAuthorizationError(ForgeFlowError):
    """A tool call was denied by deterministic authorization."""

    def __init__(self, message: str = "Tool call is not authorized") -> None:
        super().__init__(message, code="tool_authorization_denied", status_code=403)


class StructuredOutputError(ForgeFlowError):
    """The model did not return a payload that matches the required schema."""

    def __init__(self, message: str = "Model output did not match the required schema") -> None:
        super().__init__(message, code="structured_output_error", status_code=502)


class ProviderError(ForgeFlowError):
    """The configured LLM provider failed or is misconfigured."""

    def __init__(self, message: str = "LLM provider request failed") -> None:
        super().__init__(message, code="provider_error", status_code=502)


class InsufficientEvidenceError(ForgeFlowError):
    """The investigation finished without enough evidence for a confident cause."""

    def __init__(self, message: str = "Insufficient evidence for a confident conclusion") -> None:
        super().__init__(message, code="insufficient_evidence", status_code=200)
