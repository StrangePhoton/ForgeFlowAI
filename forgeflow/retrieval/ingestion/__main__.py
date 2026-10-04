"""CLI: python -m forgeflow.retrieval.ingestion --reset"""

import argparse
import asyncio

from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.observability.logging import configure_logging
from forgeflow.retrieval.ingestion import ingest_manuals


async def ingest_async(*, reset: bool) -> None:
    settings = get_settings()
    configure_logging(settings)
    database = Database(settings)
    try:
        async with database.session_factory() as session:
            await ingest_manuals(session, reset=reset)
            await session.commit()
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest fictional ForgeFlow manuals")
    parser.add_argument("--reset", action="store_true", help="Replace existing document rows")
    args = parser.parse_args()
    asyncio.run(ingest_async(reset=args.reset))


if __name__ == "__main__":
    main()
