"""Admin panel queries (read-only): clients, their reports, reading health. Never returns password hashes."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.constants import DocumentStatus
from app.core.errors import not_found
from app.db.models import AuditLog, Document, GuestSession, Parameter, User


def _since(days: int) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def overview(db: Session) -> dict:
    by_status = dict(db.execute(select(Document.status, func.count()).group_by(Document.status)).all())
    week = _since(7)
    # Test names read from reports that matched nothing in the dictionary - the list to grow it from.
    unrecognised = db.execute(
        select(func.lower(Parameter.name_raw), func.count()).where(Parameter.parameter_id.is_(None))
        .group_by(func.lower(Parameter.name_raw)).order_by(func.count().desc()).limit(15)
    ).all()
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "users_7d": db.scalar(select(func.count()).select_from(User).where(User.created_at >= week)) or 0,
        "guests_active": db.scalar(select(func.count()).select_from(GuestSession)
                                   .where(GuestSession.expires_at > datetime.now(UTC))) or 0,
        "documents": sum(by_status.values()),
        "documents_7d": db.scalar(select(func.count()).select_from(Document).where(Document.uploaded_at >= week)) or 0,
        "failed": by_status.get(DocumentStatus.FAILED, 0),
        "by_status": by_status,
        "parameters": db.scalar(select(func.count()).select_from(Parameter)) or 0,
        "unrecognised_tests": [{"name": n, "count": c} for n, c in unrecognised],
    }


def _doc_counts():
    return (select(Document.user_id, func.count().label("documents"), func.max(Document.uploaded_at).label("last_upload"))
            .where(Document.user_id.is_not(None)).group_by(Document.user_id).subquery())


def list_users(db: Session, q: str | None, limit: int, offset: int) -> dict:
    counts = _doc_counts()
    stmt = select(User, counts.c.documents, counts.c.last_upload).outerjoin(counts, counts.c.user_id == User.id)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like),
                              User.phone.like(like), func.lower(User.preferred_city).like(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(User.created_at.desc()).limit(limit).offset(offset)).all()
    return {"total": total, "items": [{**_user(u), "documents": n or 0, "last_upload": last} for u, n, last in rows]}


def _user(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "phone": u.phone, "dob": u.dob, "gender": u.gender,
            "preferred_city": u.preferred_city, "address": u.address, "height_cm": u.height_cm, "weight_kg": u.weight_kg,
            "retention_days": u.retention_days, "created_at": u.created_at}


def _documents(db: Session, *where) -> list[dict]:
    pcount = (select(Parameter.document_id, func.count().label("n"),
                     func.sum(case((Parameter.parameter_id.is_(None), 1), else_=0)).label("unmatched"))
              .group_by(Parameter.document_id).subquery())
    rows = db.execute(
        select(Document, pcount.c.n, pcount.c.unmatched, User.email).outerjoin(pcount, pcount.c.document_id == Document.id)
        .outerjoin(User, User.id == Document.user_id).where(*where).order_by(Document.uploaded_at.desc()).limit(200)
    ).all()
    return [{
        "id": d.id, "filename": d.original_filename, "status": d.status, "status_message": d.status_message,
        "category": d.report_category, "lab_name": d.lab_name, "report_date": d.report_date, "uploaded_at": d.uploaded_at,
        "pages": d.pages, "size_bytes": d.size_bytes, "parameters": n or 0, "unrecognised": int(unmatched or 0),
        "owner": email or "guest", "user_id": d.user_id,
    } for d, n, unmatched, email in rows]


def user_detail(db: Session, user_id: uuid.UUID) -> dict:
    u = db.get(User, user_id)
    if u is None:
        raise not_found("Client")
    activity = db.scalars(select(AuditLog).where(AuditLog.user_id == u.id).order_by(AuditLog.at.desc()).limit(30)).all()
    return {
        "user": _user(u),
        "documents": _documents(db, Document.user_id == u.id),
        "activity": [{"at": a.at, "action": a.action, "label": a.label, "entity": a.entity} for a in activity],
    }


def list_documents(db: Session, status: str | None) -> list[dict]:
    return _documents(db, *([Document.status == status] if status else []))
