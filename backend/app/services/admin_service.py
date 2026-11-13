"""Admin panel (FR-ADM): clients, their reports, the admin team, activity log and system status.

Roles: OWNER (ADMIN_EMAILS setting) can do everything; ADMIN (granted in the panel) can view, suspend and re-read.
Never returns password hashes. Every admin action is written to the audit log by the API layer.
"""
from __future__ import annotations

import csv
import io
import secrets
import uuid
from collections import Counter
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.constants import DocumentStatus, UserRole
from app.core.errors import AppError, not_found
from app.core.security import hash_password
from app.db.models import AuditLog, Document, GuestSession, Parameter, User
from app.db.session import engine
from app.utils import dictionaries

READ_OK = (DocumentStatus.EXTRACTED, DocumentStatus.NEEDS_VERIFICATION, DocumentStatus.VERIFIED, DocumentStatus.ANALYZED)


def _now() -> datetime:
    return datetime.now(UTC)


def _aware(d: datetime | None) -> datetime | None:
    return d.replace(tzinfo=UTC) if d is not None and d.tzinfo is None else d


def role_of(u: User) -> str:
    return get_settings().role_for(u.email, u.role)


def _owner_emails() -> list[str]:
    return [e.strip().lower() for e in get_settings().admin_emails.split(",") if e.strip()]


# ------------------------------------------------------------------ overview
def _daily(values: list[datetime], days: int) -> list[dict]:
    start = (_now() - timedelta(days=days - 1)).date()
    counts = Counter(_aware(v).date() for v in values if v is not None)
    return [{"date": (start + timedelta(days=i)).isoformat(), "count": counts.get(start + timedelta(days=i), 0)}
            for i in range(days)]


def overview(db: Session, days: int = 30) -> dict:
    by_status = dict(db.execute(select(Document.status, func.count()).group_by(Document.status)).all())
    week, since = _now() - timedelta(days=7), _now() - timedelta(days=days)
    unrecognised = db.execute(  # printed names that matched nothing - the list to grow the dictionary from
        select(func.lower(Parameter.name_raw), func.count()).where(Parameter.parameter_id.is_(None))
        .group_by(func.lower(Parameter.name_raw)).order_by(func.count().desc()).limit(15)
    ).all()
    ok = sum(by_status.get(s, 0) for s in READ_OK)
    failed = by_status.get(DocumentStatus.FAILED, 0)
    return {
        "users": db.scalar(select(func.count()).select_from(User)) or 0,
        "users_7d": db.scalar(select(func.count()).select_from(User).where(User.created_at >= week)) or 0,
        "active_7d": db.scalar(select(func.count()).select_from(User).where(User.last_login_at >= week)) or 0,
        "suspended": db.scalar(select(func.count()).select_from(User).where(User.disabled_at.is_not(None))) or 0,
        "guests_active": db.scalar(select(func.count()).select_from(GuestSession).where(GuestSession.expires_at > _now())) or 0,
        "documents": sum(by_status.values()),
        "documents_7d": db.scalar(select(func.count()).select_from(Document).where(Document.uploaded_at >= week)) or 0,
        "failed": failed,
        "read_success_rate": round(ok / (ok + failed), 3) if ok + failed else None,
        "by_status": by_status,
        "parameters": db.scalar(select(func.count()).select_from(Parameter)) or 0,
        "signups_daily": _daily(list(db.scalars(select(User.created_at).where(User.created_at >= since))), days),
        "uploads_daily": _daily(list(db.scalars(select(Document.uploaded_at).where(Document.uploaded_at >= since))), days),
        "unrecognised_tests": [{"name": n, "count": c} for n, c in unrecognised],
    }


def system_status(db: Session) -> dict:
    from app.pipelines.ocr.printed_ocr import get_printed_ocr

    s = get_settings()
    db.execute(select(1))
    return {
        "version": "0.2.0", "environment": s.app_env, "database": engine.dialect.name, "storage": s.storage_backend,
        "ocr_engine": get_printed_ocr().engine_name, "tests_in_dictionary": len(dictionaries.parameters()),
        "chatbot": "Gemini" if s.gemini_api_key else ("Claude" if s.llm_api_key else "offline answers"),
        "explanations": "Claude" if s.llm_api_key else "built-in templates",
        "centre_search": "Google Places" if s.google_places_api_key else "OpenStreetMap",
        "guest_retention_hours": s.guest_retention_hours, "max_upload_mb": s.max_upload_mb,
        "email": "Resend" if s.resend_api_key else "not connected",
        "kb_articles": _kb_count(), "llm_model": s.llm_model if s.llm_api_key else None,
        "gemini_model": s.gemini_model if s.gemini_api_key else None,
    }


def _kb_count() -> int:
    from app.rag.ingest import load_documents

    return len(load_documents())


# ------------------------------------------------------------------ clients
def _doc_counts():
    return (select(Document.user_id, func.count().label("documents"), func.max(Document.uploaded_at).label("last_upload"))
            .where(Document.user_id.is_not(None)).group_by(Document.user_id).subquery())


def _user(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "phone": u.phone, "dob": u.dob, "gender": u.gender,
            "preferred_city": u.preferred_city, "address": u.address, "height_cm": u.height_cm, "weight_kg": u.weight_kg,
            "retention_days": u.retention_days, "created_at": u.created_at, "last_login_at": u.last_login_at,
            "disabled_at": u.disabled_at, "role": role_of(u)}


_SORTS = {
    "newest": lambda c: User.created_at.desc(), "oldest": lambda c: User.created_at.asc(),
    "name": lambda c: func.lower(func.coalesce(User.full_name, User.email)).asc(),
    "reports": lambda c: func.coalesce(c.documents, 0).desc(),
    "last_active": lambda c: func.coalesce(User.last_login_at, User.created_at).desc(),
}


def _user_query(q: str | None, status: str | None, role: str | None, sort: str):
    counts = _doc_counts()
    stmt = select(User, counts.c.documents, counts.c.last_upload).outerjoin(counts, counts.c.user_id == User.id)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(User.full_name).like(like),
                              User.phone.like(like), func.lower(User.preferred_city).like(like)))
    if status == "active":
        stmt = stmt.where(User.disabled_at.is_(None))
    elif status == "suspended":
        stmt = stmt.where(User.disabled_at.is_not(None))
    if role == "admin":
        stmt = stmt.where(or_(User.role == UserRole.ADMIN, User.email.in_(_owner_emails())))
    return stmt.order_by(_SORTS.get(sort, _SORTS["newest"])(counts))


def list_users(db: Session, q: str | None, limit: int, offset: int, status: str | None = None,
               role: str | None = None, sort: str = "newest") -> dict:
    stmt = _user_query(q, status, role, sort)
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    rows = db.execute(stmt.limit(limit).offset(offset)).all()
    return {"total": total, "items": [{**_user(u), "documents": n or 0, "last_upload": last} for u, n, last in rows]}


def _cell(v) -> str:
    if v is None:
        return ""
    s = v.isoformat() if isinstance(v, date | datetime) else str(v)
    return "'" + s if s[:1] in ("=", "+", "-", "@") else s  # no spreadsheet formula injection


def users_csv(db: Session, q: str | None, status: str | None, role: str | None, sort: str) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    cols = ["full_name", "email", "phone", "gender", "dob", "preferred_city", "address", "role", "created_at",
            "last_login_at", "disabled_at"]
    w.writerow([*cols, "reports", "last_upload"])
    for u, n, last in db.execute(_user_query(q, status, role, sort)).all():
        d = _user(u)
        w.writerow([_cell(d[c]) for c in cols] + [n or 0, _cell(last)])
    return buf.getvalue()


def get_user(db: Session, user_id: uuid.UUID) -> User:
    u = db.get(User, user_id)
    if u is None:
        raise not_found("Client")
    return u


def user_detail(db: Session, user_id: uuid.UUID) -> dict:
    u = get_user(db, user_id)
    activity = db.scalars(select(AuditLog).where(AuditLog.user_id == u.id).order_by(AuditLog.at.desc()).limit(50)).all()
    return {
        "user": _user(u),
        "documents": _documents(db, Document.user_id == u.id),
        "activity": [{"at": a.at, "action": a.action, "label": a.label, "entity": a.entity} for a in activity],
    }


def set_suspended(db: Session, actor: User, user_id: uuid.UUID, suspended: bool) -> User:
    u = get_user(db, user_id)
    if u.id == actor.id:
        raise AppError("FORBIDDEN", "You can't suspend your own account.", 403)
    if suspended and role_of(u) == UserRole.OWNER:
        raise AppError("FORBIDDEN", "The owner account can't be suspended.", 403)
    if suspended and role_of(u) == UserRole.ADMIN and role_of(actor) != UserRole.OWNER:
        raise AppError("FORBIDDEN", "Only the owner can suspend another admin.", 403)
    u.disabled_at = _now() if suspended else None
    db.commit()
    return u


def reset_password(db: Session, user_id: uuid.UUID) -> tuple[User, str]:
    """Sets a one-time temporary password (no email service yet); the admin passes it on to the client."""
    u = get_user(db, user_id)
    temp = secrets.token_urlsafe(9)
    u.password_hash = hash_password(temp)  # also signs the client out everywhere (token fingerprint changes)
    db.commit()
    return u, temp


def delete_user(db: Session, actor: User, user_id: uuid.UUID) -> User:
    from app.services import user_service

    u = get_user(db, user_id)
    if u.id == actor.id or role_of(u) == UserRole.OWNER:
        raise AppError("FORBIDDEN", "This account can't be deleted from the admin panel.", 403)
    user_service.purge_user(db, u)
    return u


# ------------------------------------------------------------------ admin team
def list_admins(db: Session) -> list[dict]:
    rows = list_users(db, None, 500, 0, role="admin", sort="name")["items"]
    present = {r["email"] for r in rows}
    pending = [{"email": e, "role": UserRole.OWNER, "pending": True} for e in sorted(set(_owner_emails()) - present)]
    return [*rows, *pending]


def add_admin(db: Session, email: str, full_name: str | None, password: str | None) -> tuple[User, bool]:
    """Promote an existing account, or create a new admin account when a password is given."""
    email = email.strip().lower()
    u = db.scalar(select(User).where(User.email == email))
    created = False
    if u is None:
        if not password:
            raise AppError("NOT_FOUND", "No account with this email. Enter a password to create a new admin account.", 404)
        u = User(email=email, full_name=full_name, password_hash=hash_password(password))
        db.add(u)
        created = True
    if role_of(u) == UserRole.OWNER:
        raise AppError("CONFLICT", "This account is already the owner.", 409)
    u.role = UserRole.ADMIN
    u.disabled_at = None
    db.commit()
    return u, created


def remove_admin(db: Session, actor: User, user_id: uuid.UUID) -> User:
    u = get_user(db, user_id)
    if role_of(u) == UserRole.OWNER:
        raise AppError("FORBIDDEN", "The owner (ADMIN_EMAILS setting) can't be removed from the panel.", 403)
    if u.id == actor.id:
        raise AppError("FORBIDDEN", "You can't remove your own admin access.", 403)
    u.role = UserRole.USER
    db.commit()
    return u


# ------------------------------------------------------------------ reports
def _documents(db: Session, *where, limit: int = 200, offset: int = 0) -> list[dict]:
    pcount = (select(Parameter.document_id, func.count().label("n"),
                     func.sum(case((Parameter.parameter_id.is_(None), 1), else_=0)).label("unmatched"),
                     func.sum(case((Parameter.finding_class.in_(("OUT_OF_RANGE", "URGENT")), 1), else_=0)).label("flagged"))
              .group_by(Parameter.document_id).subquery())
    rows = db.execute(
        select(Document, pcount.c.n, pcount.c.unmatched, pcount.c.flagged, User.email)
        .outerjoin(pcount, pcount.c.document_id == Document.id).outerjoin(User, User.id == Document.user_id)
        .where(*where).order_by(Document.uploaded_at.desc()).limit(limit).offset(offset)
    ).all()
    return [{
        "id": d.id, "filename": d.original_filename, "status": d.status, "status_message": d.status_message,
        "category": d.report_category, "lab_name": d.lab_name, "report_date": d.report_date, "uploaded_at": d.uploaded_at,
        "pages": d.pages, "size_bytes": d.size_bytes, "mime": d.mime, "parameters": n or 0,
        "unrecognised": int(unmatched or 0), "out_of_range": int(flagged or 0),
        "owner": email or "guest", "user_id": d.user_id,
    } for d, n, unmatched, flagged, email in rows]


def list_documents(db: Session, status: str | None, q: str | None = None, limit: int = 100, offset: int = 0) -> dict:
    where = [Document.status == status] if status else []
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        where.append(or_(func.lower(Document.original_filename).like(like), func.lower(Document.lab_name).like(like),
                         func.lower(User.email).like(like)))
    total = db.scalar(select(func.count()).select_from(Document).outerjoin(User, User.id == Document.user_id)
                      .where(*where)) or 0
    return {"total": total, "items": _documents(db, *where, limit=limit, offset=offset)}


def get_document(db: Session, document_id: uuid.UUID) -> Document:
    d = db.get(Document, document_id)
    if d is None:
        raise not_found("Report")
    return d


def document_detail(db: Session, document_id: uuid.UUID) -> dict:
    from app.services import document_service

    d = get_document(db, document_id)
    summary = _documents(db, Document.id == d.id)[0]
    ex = document_service.extraction_out(db, d)
    return {**summary, "patient_name": d.patient_name, "doctor_name": d.doctor_name, "collected_date": d.collected_date,
            "engine": ex.engine, "warnings": ex.warnings, "results": [p.model_dump(mode="json") for p in ex.parameters]}


# ------------------------------------------------------------------ activity log
def audit_log(db: Session, q: str | None, action: str | None, limit: int, offset: int) -> dict:
    stmt = select(AuditLog, User.email).outerjoin(User, User.id == AuditLog.user_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if q and q.strip():
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(or_(func.lower(User.email).like(like), func.lower(AuditLog.label).like(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.order_by(AuditLog.at.desc()).limit(limit).offset(offset)).all()
    actions = sorted(a for a in db.scalars(select(AuditLog.action).distinct()) if a)
    return {"total": total, "actions": actions, "items": [
        {"at": a.at, "action": a.action, "label": a.label, "entity": a.entity, "entity_id": a.entity_id,
         "user_id": a.user_id, "who": email or ("guest" if a.guest_session_id else "-")} for a, email in rows]}
