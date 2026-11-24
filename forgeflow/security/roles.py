"""RBAC roles and permissions. The LLM is never consulted for authorization."""

from typing import Literal

Role = Literal["viewer", "engineer", "maintenance_manager", "admin"]
Permission = Literal[
    "equipment:read",
    "investigations:read",
    "investigations:create",
    "approvals:read",
    "approvals:decide",
    "tools:read",
    "tools:write",
    "audit:read",
]

ALL_PERMISSIONS: frozenset[Permission] = frozenset(
    {
        "equipment:read",
        "investigations:read",
        "investigations:create",
        "approvals:read",
        "approvals:decide",
        "tools:read",
        "tools:write",
        "audit:read",
    }
)

_VIEWER: frozenset[Permission] = frozenset(
    {
        "equipment:read",
        "investigations:read",
        "approvals:read",
        "tools:read",
        "audit:read",
    }
)
_ENGINEER: frozenset[Permission] = _VIEWER | frozenset({"investigations:create"})
_MANAGER: frozenset[Permission] = _ENGINEER | frozenset({"approvals:decide", "tools:write"})

ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    "viewer": _VIEWER,
    "engineer": _ENGINEER,
    "maintenance_manager": _MANAGER,
    "admin": ALL_PERMISSIONS,
}


def permissions_for(role: Role) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[role]


def has_permission(role: Role, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
