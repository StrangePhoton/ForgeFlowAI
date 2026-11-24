"""Authenticated caller. Authorization decisions use this object, not the model."""

from dataclasses import dataclass
from uuid import UUID

from forgeflow.security.roles import Permission, Role, has_permission


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    username: str
    role: Role

    def allows(self, permission: Permission) -> bool:
        return has_permission(self.role, permission)
