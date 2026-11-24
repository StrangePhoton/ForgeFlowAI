"""HMAC bearer tokens. Not a third-party IdP; sufficient for the demo API."""

import base64
import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from forgeflow.config import Settings
from forgeflow.errors import AuthenticationError
from forgeflow.security.principal import Principal
from forgeflow.security.roles import Role

_PREFIX = "ff1"


def issue_token(principal: Principal, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(principal.user_id),
        "username": principal.username,
        "role": principal.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.auth_token_ttl_seconds)).timestamp()),
    }
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(body, settings.auth_secret)
    return f"{_PREFIX}.{body}.{signature}"


def parse_token(token: str, settings: Settings) -> Principal:
    parts = token.split(".")
    if len(parts) != 3 or parts[0] != _PREFIX:
        raise AuthenticationError("Invalid access token")
    body, signature = parts[1], parts[2]
    expected = _sign(body, settings.auth_secret)
    if not hmac.compare_digest(signature, expected):
        raise AuthenticationError("Invalid access token")
    try:
        payload: dict[str, Any] = json.loads(_unb64(body))
    except (ValueError, json.JSONDecodeError) as exc:
        raise AuthenticationError("Invalid access token") from exc
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(datetime.now(UTC).timestamp()):
        raise AuthenticationError("Access token has expired")
    role = payload.get("role")
    username = payload.get("username")
    sub = payload.get("sub")
    if role not in {"viewer", "engineer", "maintenance_manager", "admin"}:
        raise AuthenticationError("Invalid access token")
    if not isinstance(username, str) or not username:
        raise AuthenticationError("Invalid access token")
    try:
        user_id = UUID(str(sub))
    except (ValueError, TypeError) as exc:
        raise AuthenticationError("Invalid access token") from exc
    return Principal(user_id=user_id, username=username, role=cast(Role, role))


def _sign(body: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), body.encode("utf-8"), hashlib.sha256).digest()
    return _b64(digest)


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
