"""Structured logging setup. Secrets must never be written to log records."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from forgeflow.config import Settings

_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_SECRET_URL_PATTERN = re.compile(r"(://[^:/?#]+):([^@/]+)@")


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_request_id(request_id: str | None) -> None:
    _REQUEST_ID.set(request_id)


def redact_secrets(value: str) -> str:
    """Mask passwords embedded in URLs such as database connection strings."""
    return _SECRET_URL_PATTERN.sub(r"\1:***@", value)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class JsonLogFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_secrets(record.getMessage()),
        }
        request_id = get_request_id()
        if request_id:
            payload["request_id"] = request_id
        if record.exc_info:
            payload["exception"] = redact_secrets(self.formatException(record.exc_info))
        extra = getattr(record, "forgeflow", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, default=str)


def configure_logging(settings: Settings) -> None:
    """Configure the root logger once per process."""
    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.database_echo else logging.WARNING
    )
