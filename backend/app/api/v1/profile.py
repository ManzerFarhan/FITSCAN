"""Profile & settings (API-17, API-18, FR-PROF-1..4)."""
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import AUTH_COOKIE, Owner, get_current_user, get_owner
from app.api.v1.documents import _read_limited
from app.core.constants import DocType, ReportCategory
from app.core.errors import AppError
from app.core.security import verify_password
from app.db.models import Comparison, Document, User
from app.db.session import get_db
from app.schemas.auth import AccountDeleteIn, PasswordChangeIn, ProfilePatch, UserOut
from app.schemas.documents import UploadResponse
from app.services import audit, document_service, user_service

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserOut)
def get_profile(user: User = Depends(get_current_user)):
    return user


@router.patch("", response_model=UserOut)
def patch_profile(body: ProfilePatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    data = body.model_dump(exclude_unset=True, exclude={"current_password"})
    if "email" in data and data["email"] and data["email"].lower() != user.email:
        if not body.current_password or not verify_password(body.current_password, user.password_hash):
            raise AppError("INVALID_CREDENTIALS", "Enter your current password to change your email.", 401)
        if db.scalar(select(User).where(User.email == data["email"].lower())):
            raise AppError("EMAIL_TAKEN", "That email is already in use.", 409)
        data["email"] = data["email"].lower()
    elif "email" in data:
        data.pop("email")
    for k, v in data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.post("/password", status_code=204)
def change_password(body: PasswordChangeIn, response: Response, user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    user_service.change_password(db, user, body.current_password, body.new_password)
    response.delete_cookie(AUTH_COOKIE, path="/")  # all sessions invalidated; log in again
    response.status_code = 204
    return response


@router.post("/historical-documents", response_model=UploadResponse, status_code=202)  # API-18
async def upload_historical(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: DocType = Form(DocType.LAB_REPORT),
    report_date: date | None = Form(None),
    category: ReportCategory | None = Form(None),
    description: str | None = Form(None, max_length=2000),
    owner: Owner = Depends(get_owner),
    db: Session = Depends(get_db),
):
    if owner.user is None:
        raise AppError("AUTH_REQUIRED", "Please log in to build your medical history.", 401)
    if report_date and report_date > date.today():
        raise AppError("VALIDATION_ERROR", "The report date can't be in the future.", 422)
    data = await _read_limited(file)
    doc = document_service.create_document(db, owner, data, file.filename or "upload", doc_type, report_date,
                                           category.value if category else None, description)
    document_service.run_or_schedule(background_tasks, doc.id)
    db.refresh(doc)
    return UploadResponse(document_id=doc.id, status=doc.status)


@router.get("/records")  # FR-PROF-3 consolidated view
def records(owner: Owner = Depends(get_owner), db: Session = Depends(get_db)) -> dict:
    docs = db.scalars(owner.scope(select(Document), Document).order_by(Document.uploaded_at.desc())).all()
    comps = db.scalars(owner.scope(select(Comparison), Comparison).order_by(Comparison.created_at.desc())).all()
    return {
        "lab_reports": len(docs),
        "analyses": sum(d.status == "ANALYZED" for d in docs),
        "comparisons": [{"id": str(c.id), "created_at": c.created_at.isoformat(), "documents": len(c.document_ids),
                         "summary": c.summary_text} for c in comps[:10]],
    }


@router.delete("", status_code=204)  # account deletion (FR-PROF-4 privacy)
def delete_account(body: AccountDeleteIn, response: Response, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    user_service.delete_account(db, user, body.password)
    response.delete_cookie(AUTH_COOKIE, path="/")
    response.status_code = 204
    return response


@router.delete("/documents", status_code=200)  # delete all my documents
def delete_all_documents(owner: Owner = Depends(get_owner), db: Session = Depends(get_db)) -> dict:
    docs = db.scalars(owner.scope(select(Document), Document)).all()
    for d in docs:
        document_service.delete_document(db, d)
    audit.record(db, owner, "DELETE_ALL", "document", None, f"Deleted {len(docs)} documents")
    return {"deleted": len(docs)}
