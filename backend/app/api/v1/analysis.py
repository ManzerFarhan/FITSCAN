"""AI analysis, chat and PDF summary (API-06..09)."""
import uuid

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import Owner, get_owner, rate_limit
from app.core.constants import DISCLAIMER_TEXT
from app.core.errors import AppError
from app.db.models import ChatMessage, Comparison
from app.db.session import get_db
from app.services import analysis_service, audit, comparison_service
from app.services.document_service import get_owned
from app.services.pdf_report_service import build_pdf

router = APIRouter(prefix="/documents/{document_id}", tags=["analysis"])


def _analysis_out(a) -> dict:
    return {"id": str(a.id), "document_id": str(a.document_id), "summary": a.summary_json,
            "observations": a.observations_json, "sources": a.sources_json, "model": a.model,
            "prompt_version": a.prompt_version, "created_at": a.created_at.isoformat(),
            "source_tag": "AI_GENERATED", "disclaimer": DISCLAIMER_TEXT}


@router.post("/analysis", status_code=201, dependencies=[Depends(rate_limit("analysis", 20))])  # API-06
def create_analysis(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    doc = get_owned(db, owner, document_id)
    return _analysis_out(analysis_service.generate_analysis(db, owner, doc))


@router.get("/analysis")  # API-07
def get_analysis(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    doc = get_owned(db, owner, document_id)
    a = analysis_service.latest_analysis(db, doc)
    if a is None:
        raise AppError("NOT_FOUND", "No analysis yet for this document.", 404)
    return _analysis_out(a)


class ChatIn(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


def _msg_out(m: ChatMessage) -> dict:
    return {"id": str(m.id), "role": m.role, "content": m.content, "sources": m.sources_json,
            "created_at": m.created_at.isoformat(), "source_tag": "AI_GENERATED" if m.role == "assistant" else None}


@router.post("/chat", dependencies=[Depends(rate_limit("chat", 20))])  # API-08
def chat(document_id: uuid.UUID, body: ChatIn, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    doc = get_owned(db, owner, document_id)
    if not any(p.verified for p in doc.parameters):
        raise AppError("NOT_VERIFIED", "Please confirm the extracted values before asking questions.", 409)
    return _msg_out(analysis_service.chat(db, owner, doc, body.question))


@router.get("/chat")
def chat_history(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    doc = get_owned(db, owner, document_id)
    msgs = db.scalars(select(ChatMessage).where(ChatMessage.document_id == doc.id).order_by(ChatMessage.created_at)).all()
    return [_msg_out(m) for m in msgs]


@router.get("/summary.pdf")  # API-09
def summary_pdf(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    doc = get_owned(db, owner, document_id)
    a = analysis_service.latest_analysis(db, doc)
    if a is None:
        raise AppError("NOT_FOUND", "Generate the AI analysis first, then download the summary.", 404)
    comparison = None
    comps = db.scalars(owner.scope(select(Comparison), Comparison).order_by(Comparison.created_at.desc())).all()
    for c in comps:
        if str(doc.id) in c.document_ids:
            comparison = c.result_json
            break
    pdf = build_pdf(doc, a, comparison)
    audit.record(db, owner, "SUMMARY_DOWNLOAD", "document", doc.id, f"Downloaded PDF summary: {doc.original_filename}")
    name = f"FITSCAN-summary-{(doc.report_date or doc.uploaded_at.date()).isoformat()}.pdf"
    return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="{name}"'})


comparisons_router = APIRouter(prefix="/comparisons", tags=["comparisons"])


class ComparisonIn(BaseModel):
    document_ids: list[uuid.UUID] = Field(..., min_length=2, max_length=10)


def _comp_out(c: Comparison) -> dict:
    return {"id": str(c.id), "document_ids": c.document_ids, "result": c.result_json,
            "created_at": c.created_at.isoformat(), "disclaimer": DISCLAIMER_TEXT}


@comparisons_router.post("", status_code=201)  # API-14
def create_comparison(body: ComparisonIn, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    return _comp_out(comparison_service.create(db, owner, body.document_ids))


@comparisons_router.get("")
def list_comparisons(owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    comps = db.scalars(owner.scope(select(Comparison), Comparison).order_by(Comparison.created_at.desc()).limit(20)).all()
    return [_comp_out(c) for c in comps]
