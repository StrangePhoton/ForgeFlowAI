"""Seed demo operator accounts into PostgreSQL."""

from datetime import UTC, datetime

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import UserAccount
from forgeflow.security.accounts import demo_directory


async def persist_demo_users(session: AsyncSession) -> int:
    await session.execute(delete(UserAccount))
    now = datetime.now(UTC)
    accounts = demo_directory().accounts()
    for account in accounts:
        session.add(
            UserAccount(
                id=account.principal.user_id,
                username=account.principal.username,
                password_hash=account.password_hash,
                role=account.principal.role,
                created_at=now,
                is_active=True,
            )
        )
    return len(accounts)
