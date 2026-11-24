"""Password hashing with stdlib PBKDF2. No credentials in logs."""

import hashlib
import hmac
import os

_ITERATIONS = 120_000
_ALGORITHM = "pbkdf2_sha256"


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    raw_salt = salt if salt is not None else os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), raw_salt, _ITERATIONS)
    return f"{_ALGORITHM}${_ITERATIONS}${raw_salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) != 4 or parts[0] != _ALGORITHM:
        return False
    try:
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected = bytes.fromhex(parts[3])
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)
