"""Password hashing (bcrypt) and JWT tokens (NFR-03).

Tokens carry a fingerprint of the current password hash, so changing or resetting the password
invalidates every existing session and reset link.
"""
import hashlib
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import get_settings

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode()[:72], password_hash.encode())
    except ValueError:
        return False


def fingerprint(password_hash: str) -> str:
    return hashlib.sha256(password_hash.encode()).hexdigest()[:16]


def create_token(user_id: uuid.UUID, password_hash: str, purpose: str = "access", minutes: int | None = None) -> str:
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes or s.jwt_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": exp, "purpose": purpose, "fp": fingerprint(password_hash)},
                      s.jwt_secret, ALGORITHM)


def decode_token(token: str, purpose: str = "access") -> tuple[uuid.UUID, str] | None:
    """Returns (user_id, password fingerprint) or None."""
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[ALGORITHM])
        if payload.get("purpose") != purpose:
            return None
        return uuid.UUID(payload["sub"]), payload.get("fp", "")
    except (JWTError, KeyError, ValueError):
        return None


# ---------------------------------------------------------------- rate limiting (P4-16)
_hits: dict[str, deque] = defaultdict(deque)


def rate_limited(key: str, limit: int, window_s: int = 60) -> bool:
    """Sliding-window limiter (in-process; use Redis for multi-instance deployments)."""
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > window_s:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def reset_rate_limits() -> None:
    _hits.clear()
