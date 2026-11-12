"""Retention (BR-15, FR-PROF-4; P4-11): expire guest sessions and apply user retention preferences."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models import Document, GuestSession, User
from app.services.storage import get_storage

log = get_logger("retention")


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def cleanup(db: Session, now: datetime | None = None) -> dict:
    now = now or datetime.now(timezone.utc)
    storage = get_storage()
    keys: list[str] = []

    expired = [g for g in db.scalars(select(GuestSession)).all() if _aware(g.expires_at) <= now]
    for g in expired:
        keys += list(db.scalars(select(Document.storage_key).where(Document.guest_session_id == g.id)))
        db.delete(g)  # guest documents and everything derived cascade

    user_docs = 0
    for u in db.scalars(select(User).where(User.retention_days.is_not(None))).all():
        cutoff = now - timedelta(days=u.retention_days)
        for d in db.scalars(select(Document).where(Document.user_id == u.id)).all():
            if _aware(d.uploaded_at) < cutoff:
                keys.append(d.storage_key)
                db.delete(d)
                user_docs += 1
    db.commit()
    for k in keys:
        try:
            storage.delete(k)
        except Exception:
            log.warning("Stored object could not be deleted")
    result = {"guest_sessions": len(expired), "user_documents": user_docs, "files": len(keys)}
    log.info("Retention cleanup removed %s guest sessions", len(expired))
    return result
