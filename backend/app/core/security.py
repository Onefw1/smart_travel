import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

password_hasher = PasswordHasher(type=Type.ID)
_dummy_hash = password_hasher.hash(secrets.token_urlsafe(32))
SESSION_TTL_SECONDS = 8 * 60 * 60


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, encoded: str | None) -> bool:
    try:
        valid = password_hasher.verify(encoded or _dummy_hash, password)
        return valid and encoded is not None
    except (VerificationError, InvalidHashError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


def csrf_matches(actual: str | None, expected: str) -> bool:
    return actual is not None and secrets.compare_digest(actual.encode(), expected.encode())
