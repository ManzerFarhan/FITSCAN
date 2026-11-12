"""Audit log (DB-14) - security/privacy trail of uploads, confirmations and deletions. No PHI in labels."""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.models import AuditLog


def record(db: Session, owner, action: str, entity: str, entity_id=None, label: str | None = None,
           commit: bool = True) -> None:
    db.add(AuditLog(user_id=owner.user_id, guest_session_id=owner.guest_session_id, action=action, entity=entity,
                    entity_id=str(entity_id) if entity_id else None, label=(label or "")[:255] or None))
    if commit:
        db.commit()
