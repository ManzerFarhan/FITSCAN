"""Admin panel API (FR-ADM-1..12). OWNER = ADMIN_EMAILS; ADMIN = granted in the panel. Every action is audit-logged."""
import uuid
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.api.deps import Owner, admin_required, owner_required
from app.core.constants import DocumentStatus
from app.db.models import User
from app.db.session import get_db
from app.services import admin_service as svc
from app.services import audit, document_service
from app.services.storage import get_storage

router = APIRouter(prefix="/admin", tags=["admin"])


def _log(db: Session, admin: User, action: str, entity: str, entity_id, label: str) -> None:
    audit.record(db, Owner(user=admin), action, entity, entity_id, label)


# ------------------------------------------------------------------ overview & system
@router.get("/overview")
def overview(days: int = Query(30, ge=7, le=90), _: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return svc.overview(db, days)


@router.get("/system")
def system(_: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return svc.system_status(db)


# ------------------------------------------------------------------ clients
_USER_FILTERS = {"q": Query(None, max_length=200), "status": Query(None, pattern="^(active|suspended)$"),
                 "role": Query(None, pattern="^admin$"), "sort": Query("newest", pattern="^(newest|oldest|name|reports|last_active)$")}


@router.get("/users")
def users(q: str | None = _USER_FILTERS["q"], status: str | None = _USER_FILTERS["status"],
          role: str | None = _USER_FILTERS["role"], sort: str = _USER_FILTERS["sort"],
          limit: int = Query(25, ge=1, le=200), offset: int = Query(0, ge=0),
          _: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return svc.list_users(db, q, limit, offset, status, role, sort)


@router.get("/users.csv")
def users_csv(q: str | None = _USER_FILTERS["q"], status: str | None = _USER_FILTERS["status"],
              role: str | None = _USER_FILTERS["role"], sort: str = _USER_FILTERS["sort"],
              admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> Response:
    body = svc.users_csv(db, q, status, role, sort)
    _log(db, admin, "ADMIN_EXPORT", "user", None, "Exported the client list (CSV)")
    return Response(body, media_type="text/csv", headers={
        "Content-Disposition": f'attachment; filename="fitscan-clients-{date.today().isoformat()}.csv"',
        "Cache-Control": "private, no-store"})


@router.get("/users/{user_id}")
def user_detail(user_id: uuid.UUID, admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    out = svc.user_detail(db, user_id)
    _log(db, admin, "ADMIN_VIEW", "user", user_id, "Opened client details")
    return out


@router.post("/users/{user_id}/suspend")
def suspend(user_id: uuid.UUID, admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    svc.set_suspended(db, admin, user_id, True)
    _log(db, admin, "ADMIN_SUSPEND", "user", user_id, "Suspended a client account")
    return {"ok": True}


@router.post("/users/{user_id}/reactivate")
def reactivate(user_id: uuid.UUID, admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    svc.set_suspended(db, admin, user_id, False)
    _log(db, admin, "ADMIN_REACTIVATE", "user", user_id, "Reactivated a client account")
    return {"ok": True}


@router.post("/users/{user_id}/reset-password")
def reset_password(user_id: uuid.UUID, admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> dict:
    _, temp = svc.reset_password(db, user_id)
    _log(db, admin, "ADMIN_RESET_PASSWORD", "user", user_id, "Set a temporary password for a client")
    return {"temporary_password": temp}


@router.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: uuid.UUID, admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> Response:
    svc.delete_user(db, admin, user_id)
    _log(db, admin, "ADMIN_DELETE_USER", "user", user_id, "Deleted a client account and all its data")
    return Response(status_code=204)


# ------------------------------------------------------------------ admin team
class AdminIn(BaseModel):
    email: EmailStr
    full_name: str | None = Field(None, max_length=200)
    password: str | None = Field(None, min_length=8, max_length=128)  # only to create a new account


@router.get("/admins")
def admins(_: User = Depends(admin_required), db: Session = Depends(get_db)) -> list[dict]:
    return svc.list_admins(db)


@router.post("/admins", status_code=201)
def add_admin(body: AdminIn, admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> dict:
    u, created = svc.add_admin(db, body.email, body.full_name, body.password)
    _log(db, admin, "ADMIN_GRANT", "user", u.id, "Created an admin account" if created else "Gave admin access")
    return {"id": u.id, "email": u.email, "created": created}


@router.delete("/admins/{user_id}", status_code=204)
def remove_admin(user_id: uuid.UUID, admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> Response:
    svc.remove_admin(db, admin, user_id)
    _log(db, admin, "ADMIN_REVOKE", "user", user_id, "Removed admin access")
    return Response(status_code=204)


# ------------------------------------------------------------------ reports
@router.get("/documents")
def documents(status: str | None = Query(None, max_length=32), q: str | None = Query(None, max_length=200),
              limit: int = Query(25, ge=1, le=200), offset: int = Query(0, ge=0),
              _: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return svc.list_documents(db, status, q, limit, offset)


@router.get("/documents/{document_id}")
def document_detail(document_id: uuid.UUID, admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    out = svc.document_detail(db, document_id)
    _log(db, admin, "ADMIN_VIEW", "document", document_id, "Opened a client report")
    return out


@router.get("/documents/{document_id}/file")
def document_file(document_id: uuid.UUID, download: bool = False, admin: User = Depends(admin_required),
                  db: Session = Depends(get_db)) -> Response:
    d = svc.get_document(db, document_id)
    _log(db, admin, "ADMIN_VIEW_FILE", "document", document_id, "Opened a client's original file")
    return Response(get_storage().get(d.storage_key), media_type=d.mime, headers={
        "Content-Disposition": f'{"attachment" if download else "inline"}; filename="{d.original_filename}"',
        "Cache-Control": "private, no-store"})


@router.post("/documents/{document_id}/reprocess", status_code=202)
def reprocess(document_id: uuid.UUID, background_tasks: BackgroundTasks, admin: User = Depends(admin_required),
              db: Session = Depends(get_db)) -> dict:
    """Read a report again (e.g. after the dictionary or OCR improved)."""
    d = svc.get_document(db, document_id)
    d.status, d.status_message = DocumentStatus.UPLOADED, None
    db.commit()
    _log(db, admin, "ADMIN_REPROCESS", "document", document_id, "Re-read a client report")
    document_service.run_or_schedule(background_tasks, d.id)
    return {"ok": True}


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> Response:
    document_service.delete_document(db, svc.get_document(db, document_id))
    _log(db, admin, "ADMIN_DELETE_DOCUMENT", "document", document_id, "Deleted a client report")
    return Response(status_code=204)


# ------------------------------------------------------------------ activity log
@router.get("/audit")
def audit_log(q: str | None = Query(None, max_length=200), action: str | None = Query(None, max_length=64),
              limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
              _: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return svc.audit_log(db, q, action, limit, offset)


# ------------------------------------------------------------------ dataset (what FITSCAN knows)
@router.get("/dataset")
def dataset(_: User = Depends(admin_required)) -> dict:
    from app.services import dataset_service

    return dataset_service.dataset()


@router.get("/dataset/check")
def dataset_check(name: str = Query(..., min_length=1, max_length=200), _: User = Depends(admin_required)) -> dict:
    from app.services import dataset_service

    return dataset_service.check_name(name)


# ------------------------------------------------------------------ weekly summary email
@router.get("/weekly-summary")
def weekly_summary_preview(_: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    from app.core.config import get_settings
    from app.services import weekly_summary as ws

    s = get_settings()
    summary = ws.build(db)
    return {"configured": bool(s.resend_api_key), "recipients": ws.recipients(), "weekday": s.weekly_summary_weekday,
            "last_sent": ws.last_sent(db), "summary": summary,
            "html": ws.render_html(summary, s.frontend_origin.split(",")[0].strip().rstrip("/") + "/admin")}


@router.post("/weekly-summary/send")
def weekly_summary_send(admin: User = Depends(owner_required), db: Session = Depends(get_db)) -> dict:
    from app.services import weekly_summary as ws

    out = ws.send(db)
    _log(db, admin, "ADMIN_SEND_SUMMARY", "email", None, "Sent the weekly summary email now")
    return {"sent_to": out["sent_to"]}
