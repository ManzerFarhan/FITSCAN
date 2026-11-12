"""Dashboard API (API-15) - real aggregation over the caller's own data."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Owner, get_owner
from app.db.session import get_db
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def get_dashboard(owner: Owner = Depends(get_owner), db: Session = Depends(get_db)) -> dict:
    return dashboard_service.build(db, owner)
