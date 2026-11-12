"""Accounts: registration, login, guest->account migration, password reset, deletion (FR-PROF-4..6)."""
from __future__ import annotations

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.security import create_token, decode_token, fingerprint, hash_password, verify_password
from app.db.models import AuditLog, Comparison, Document, GuestSession, User
from app.services.storage import get_storage

log = get_logger("users")
RESET_MINUTES = 30


def register(db: Session, email: str, password: str, full_name: str | None) -> User:
    email = email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise AppError("EMAIL_TAKEN", "An account with this email already exists. Try logging in.", 409)
    user = User(email=email, password_hash=hash_password(password), full_name=full_name)
    db.add(user)
    db.commit()
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Email or password is incorrect.", 401)
    return user


def migrate_guest(db: Session, guest: GuestSession | None, user: User) -> int:
    """FR-PROF-6: move the guest session's data into the account."""
    if guest is None:
        return 0
    n = 0
    for model in (Document, Comparison, AuditLog):
        res = db.execute(update(model).where(model.guest_session_id == guest.id)
                         .values(user_id=user.id, guest_session_id=None))
        if model is Document:
            n = res.rowcount or 0
    db.delete(guest)
    db.commit()
    return n


def access_token(user: User) -> str:
    return create_token(user.id, user.password_hash)


def request_reset(db: Session, email: str) -> str | None:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None:
        return None
    return create_token(user.id, user.password_hash, purpose="reset", minutes=RESET_MINUTES)


def confirm_reset(db: Session, token: str, new_password: str) -> User:
    decoded = decode_token(token, purpose="reset")
    user = db.get(User, decoded[0]) if decoded else None
    if user is None or fingerprint(user.password_hash) != decoded[1]:
        raise AppError("INVALID_TOKEN", "This reset link is invalid or has already been used.", 400)
    user.password_hash = hash_password(new_password)
    db.commit()
    return user


def change_password(db: Session, user: User, current: str, new: str) -> None:
    if not verify_password(current, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Current password is incorrect.", 401)
    user.password_hash = hash_password(new)
    db.commit()


def delete_account(db: Session, user: User, password: str) -> None:
    if not verify_password(password, user.password_hash):
        raise AppError("INVALID_CREDENTIALS", "Password is incorrect.", 401)
    keys = list(db.scalars(select(Document.storage_key).where(Document.user_id == user.id)))
    db.delete(user)  # documents, parameters, analyses, recs, comparisons cascade in the DB
    db.commit()
    storage = get_storage()
    for k in keys:
        try:
            storage.delete(k)
        except Exception:
            log.warning("Could not delete a stored object during account deletion")
