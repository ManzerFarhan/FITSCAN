"""Request dependencies: DB session and the data *owner* (registered user or guest session).

Every query on user data MUST go through `Owner.scope(...)` (NFR-04 per-user isolation).
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request, Response
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import GuestSession, User
from app.db.session import get_db

GUEST_COOKIE = "fitscan_guest"
AUTH_COOKIE = "fitscan_auth"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class Owner:
    user: User | None = None
    guest: GuestSession | None = None

    @property
    def user_id(self) -> uuid.UUID | None:
        return self.user.id if self.user else None

    @property
    def guest_session_id(self) -> uuid.UUID | None:
        return None if self.user else (self.guest.id if self.guest else None)

    @property
    def is_guest(self) -> bool:
        return self.user is None

    def scope(self, stmt: Select, model) -> Select:
        if self.user is not None:
            return stmt.where(model.user_id == self.user.id)
        return stmt.where(model.guest_session_id == self.guest.id)

    def owns(self, obj) -> bool:
        if self.user is not None:
            return obj.user_id == self.user.id
        return obj.guest_session_id is not None and obj.guest_session_id == self.guest.id

    def stamp(self, obj) -> None:
        obj.user_id = self.user_id
        obj.guest_session_id = self.guest_session_id


def _cookie_kwargs() -> dict:
    s = get_settings()
    return {"httponly": True, "samesite": "lax", "secure": s.is_production, "path": "/"}


def _resolve_user(request: Request, db: Session) -> User | None:
    from app.core.security import decode_token, fingerprint  # local import: avoid cycles

    token = request.cookies.get(AUTH_COOKIE)
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:]
    if not token:
        return None
    decoded = decode_token(token)
    if not decoded:
        return None
    user = db.get(User, decoded[0])
    if user is None or fingerprint(user.password_hash) != decoded[1]:
        return None  # password changed since the token was issued
    return user


def rate_limit(name: str, limit: int, window_s: int = 60):
    """Dependency factory: per-client-IP limit for sensitive endpoints."""
    from app.core.errors import AppError
    from app.core.security import rate_limited

    def _dep(request: Request) -> None:
        ip = request.client.host if request.client else "unknown"
        if rate_limited(f"{name}:{ip}", limit, window_s):
            raise AppError("RATE_LIMITED", "Too many requests. Please wait a minute and try again.", 429)

    return _dep


def _resolve_guest(request: Request, response: Response, db: Session) -> GuestSession:
    s = get_settings()
    now = datetime.now(UTC)
    token = request.cookies.get(GUEST_COOKIE) or request.headers.get("x-guest-token")
    if token:
        guest = db.scalar(select(GuestSession).where(GuestSession.token_hash == hash_token(token)))
        if guest is not None:
            expires = guest.expires_at if guest.expires_at.tzinfo else guest.expires_at.replace(tzinfo=UTC)
            if expires > now:
                return guest
    token = secrets.token_urlsafe(32)
    guest = GuestSession(
        token_hash=hash_token(token), expires_at=now + timedelta(hours=s.guest_retention_hours)
    )
    db.add(guest)
    db.commit()
    response.set_cookie(GUEST_COOKIE, token, max_age=s.guest_retention_hours * 3600, **_cookie_kwargs())
    response.headers["X-Guest-Token"] = token
    return guest


def get_owner(request: Request, response: Response, db: Session = Depends(get_db)) -> Owner:
    user = _resolve_user(request, db)
    if user is not None:
        return Owner(user=user)
    return Owner(guest=_resolve_guest(request, response, db))


def get_current_user(owner: Owner = Depends(get_owner)) -> User:
    from app.core.errors import AppError

    if owner.user is None:
        raise AppError("AUTH_REQUIRED", "Please log in to continue.", 401)
    return owner.user


def login_required(feature: str):
    """'Log in to unlock' features (Tests & Centres, the assistant): guests get a friendly 401."""
    def dep(owner: Owner = Depends(get_owner)) -> Owner:
        from app.core.errors import AppError

        if owner.user is None:
            raise AppError("LOGIN_TO_UNLOCK", f"Log in or create a free account to use {feature}.", 401,
                           {"feature": feature})
        return owner
    return dep


def admin_required(owner: Owner = Depends(get_owner)) -> User:
    """Admin panel: a signed-in account listed in ADMIN_EMAILS. Everyone else gets 401/403."""
    from app.core.errors import AppError

    if owner.user is None:
        raise AppError("AUTH_REQUIRED", "Please log in to continue.", 401)
    if not get_settings().is_admin_email(owner.user.email):
        raise AppError("FORBIDDEN", "This page is for FITSCAN administrators only.", 403)
    return owner.user
