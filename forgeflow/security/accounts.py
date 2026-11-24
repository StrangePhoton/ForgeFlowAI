"""Demo operator accounts. Passwords are local-development secrets, not production IAM."""

from dataclasses import dataclass
from typing import cast
from uuid import uuid5

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forgeflow.domain.models import UserAccount
from forgeflow.domain.seed.constants import SEED_NAMESPACE
from forgeflow.security.passwords import hash_password, verify_password
from forgeflow.security.principal import Principal
from forgeflow.security.roles import Role

DEMO_USERS: tuple[tuple[str, str, Role], ...] = (
    ("viewer", "viewer-dev", "viewer"),
    ("engineer", "engineer-dev", "engineer"),
    ("manager", "manager-dev", "maintenance_manager"),
    ("admin", "admin-dev", "admin"),
)


@dataclass(frozen=True)
class Account:
    principal: Principal
    password_hash: str


class UserDirectory:
    """In-process username/password directory used by login and tests."""

    def __init__(self, accounts: list[Account]) -> None:
        self._by_username = {item.principal.username: item for item in accounts}

    def authenticate(self, username: str, password: str) -> Principal | None:
        account = self._by_username.get(username.strip())
        if account is None or not verify_password(password, account.password_hash):
            return None
        return account.principal

    def get(self, username: str) -> Principal | None:
        account = self._by_username.get(username)
        if account is None:
            return None
        return account.principal

    def accounts(self) -> list[Account]:
        return list(self._by_username.values())


_DIRECTORY: UserDirectory | None = None


def demo_directory() -> UserDirectory:
    """Return the process-wide demo directory. Hashes are computed once."""
    global _DIRECTORY
    if _DIRECTORY is None:
        accounts: list[Account] = []
        for username, password, role in DEMO_USERS:
            user_id = uuid5(SEED_NAMESPACE, f"user|{username}")
            accounts.append(
                Account(
                    principal=Principal(user_id=user_id, username=username, role=role),
                    password_hash=hash_password(password),
                )
            )
        _DIRECTORY = UserDirectory(accounts)
    return _DIRECTORY


async def authenticate_user(
    session: AsyncSession, username: str, password: str
) -> Principal | None:
    """Authenticate against the seeded `users` table."""
    row = await session.scalar(select(UserAccount).where(UserAccount.username == username.strip()))
    if row is None or not row.is_active:
        return None
    if not verify_password(password, row.password_hash):
        return None
    if row.role not in {"viewer", "engineer", "maintenance_manager", "admin"}:
        return None
    return Principal(user_id=row.id, username=row.username, role=cast(Role, row.role))


def principal_for_role(role: Role) -> Principal:
    for username, _password, account_role in DEMO_USERS:
        if account_role == role:
            found = demo_directory().get(username)
            if found is not None:
                return found
    raise KeyError(role)
