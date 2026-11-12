"""Centre finder (API-13). Log in to unlock."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import Owner, login_required
from app.db.session import get_db
from app.services import centre_service

router = APIRouter(prefix="/centres", tags=["centres"])
_member = login_required("Tests & Centres")


@router.post("/search")
def search(body: centre_service.SearchRequest, owner: Owner = Depends(_member), db: Session = Depends(get_db)):
    return centre_service.search(db, owner, body)


@router.get("/location", response_model=centre_service.LocationOut)
def suggested_location(owner: Owner = Depends(_member), db: Session = Depends(get_db)):
    return centre_service.resolve_location(db, owner)
