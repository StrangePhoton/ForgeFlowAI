"""Structured logging tests."""

import json
import logging

from forgeflow.observability.logging import JsonLogFormatter, redact_secrets


def test_redact_secrets_masks_url_password() -> None:
    raw = "postgresql+asyncpg://forgeflow:super-secret@localhost:5432/forgeflow"
    redacted = redact_secrets(raw)
    assert "super-secret" not in redacted
    assert redacted.startswith("postgresql+asyncpg://forgeflow:***@")


def test_json_formatter_emits_object() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="forgeflow.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="connected to postgresql://user:hunter2@db/app",
        args=(),
        exc_info=None,
    )
    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "forgeflow.test"
    assert "hunter2" not in payload["message"]
    assert "timestamp" in payload
