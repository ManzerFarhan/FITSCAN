"""Site-wide assistant API (floating chatbot)."""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import Owner, login_required, rate_limit
from app.core.constants import DISCLAIMER_TEXT
from app.db.session import get_db
from app.services import assistant_service
from app.services.assistant_service import Turn
from app.services.document_service import get_owned

router = APIRouter(prefix="/assistant", tags=["assistant"])


class AssistantIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    page: str | None = Field(None, max_length=200)
    document_id: uuid.UUID | None = None
    history: list[Turn] = Field(default_factory=list, max_length=12)


@router.post("/chat", dependencies=[Depends(rate_limit("assistant", 30))])
def chat(body: AssistantIn, owner: Owner = Depends(login_required("the FITSCAN assistant")),
         db: Session = Depends(get_db)) -> dict:
    doc = get_owned(db, owner, body.document_id) if body.document_id else None  # 404 if not the caller's
    reply = assistant_service.answer(db, body.question, body.page, body.history, doc)
    return {**reply.model_dump(mode="json"), "disclaimer": DISCLAIMER_TEXT}


class TermIn(BaseModel):
    term: str = Field(..., min_length=1, max_length=300)


@router.post("/explain-term", dependencies=[Depends(rate_limit("explain_term", 60))])
def explain_term(body: TermIn) -> dict:
    """'What is this?' for a row FITSCAN couldn't recognise: meaning + closest dictionary tests (user chooses)."""
    return {**assistant_service.explain_term(body.term).model_dump(mode="json"), "disclaimer": DISCLAIMER_TEXT}


@router.get("/suggestions")
def suggestions(page: str | None = None) -> dict:
    return {"suggestions": assistant_service._suggestions(page)}
