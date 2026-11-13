"""Admin panel API (read-only). Only accounts listed in ADMIN_EMAILS; every client view is audit-logged."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import Owner, admin_required
from app.db.models import User
from app.db.session import get_db
from app.services import admin_service, audit

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
def overview(_: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return admin_service.overview(db)


@router.get("/users")
def users(q: str | None = Query(None, max_length=200), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
          _: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    return admin_service.list_users(db, q, limit, offset)


@router.get("/users/{user_id}")
def user_detail(user_id: uuid.UUID, admin: User = Depends(admin_required), db: Session = Depends(get_db)) -> dict:
    out = admin_service.user_detail(db, user_id)
    audit.record(db, Owner(user=admin), "ADMIN_VIEW", "user", user_id, "Admin opened client details")
    return out


@router.get("/documents")
def documents(status: str | None = Query(None, max_length=32), _: User = Depends(admin_required),
              db: Session = Depends(get_db)) -> list[dict]:
    return admin_service.list_documents(db, status)
