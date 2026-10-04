"""CLI: python -m forgeflow.domain.seed --reset"""

import argparse
import asyncio
from datetime import UTC, datetime

from forgeflow.config import get_settings
from forgeflow.db.session import Database
from forgeflow.domain.seed.generate import generate_plant
from forgeflow.domain.seed.persist import persist_plant
from forgeflow.observability.logging import configure_logging, get_logger

logger = get_logger(__name__)


async def seed_async(*, reset: bool, now: datetime | None) -> None:
    settings = get_settings()
    configure_logging(settings)
    snapshot = generate_plant(now=now)
    database = Database(settings)
    try:
        async with database.session_factory() as session:
            await persist_plant(session, snapshot, reset=reset)
            await session.commit()
        logger.info(
            "seed_complete",
            extra={
                "forgeflow": {
                    "generated_at": snapshot.generated_at.isoformat(),
                    "equipment": len(snapshot.equipment),
                    "readings": len(snapshot.readings),
                    "alarms": len(snapshot.alarms),
                }
            },
        )
    finally:
        await database.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Load synthetic ForgeFlow industrial data")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing industrial rows before inserting the snapshot",
    )
    args = parser.parse_args()
    asyncio.run(seed_async(reset=args.reset, now=datetime.now(UTC)))


if __name__ == "__main__":
    main()
