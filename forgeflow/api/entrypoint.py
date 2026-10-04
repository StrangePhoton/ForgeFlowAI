"""Container/process startup: migrate, then serve the API.

A Python entrypoint avoids Windows CRLF breaking a ``#!/bin/sh`` shebang
inside Linux images (``exec ...: no such file or directory``).

Migrations run in a subprocess so Alembic's ``asyncio.run`` cannot poison
the uvicorn event loop in this process.
"""

import os
import subprocess
import sys
from pathlib import Path

import uvicorn

from forgeflow.observability.logging import get_logger

logger = get_logger(__name__)

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8000


def run_migrations() -> None:
    """Apply Alembic migrations in an isolated interpreter."""
    alembic = Path(sys.executable).with_name("alembic")
    subprocess.run([str(alembic), "upgrade", "head"], check=True)


def main() -> None:
    host = os.environ.get("FORGEFLOW_API_HOST", DEFAULT_HOST)
    port = int(os.environ.get("FORGEFLOW_API_PORT", str(DEFAULT_PORT)))
    logger.info("running_migrations")
    run_migrations()
    logger.info("starting_api", extra={"forgeflow": {"host": host, "port": port}})
    uvicorn.run("apps.api.main:app", host=host, port=port)


if __name__ == "__main__":
    main()
