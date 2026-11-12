"""Documents API (API-01..05, 10, 11)."""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Query, Response, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import Owner, get_owner, rate_limit
from app.core.config import get_settings
from app.core.constants import DocType, DocumentStatus, ReportCategory
from app.core.errors import AppError
from app.db.session import get_db
from app.pipelines.preprocessing.pdf_loader import render_page_png
from app.schemas.documents import DocumentList, DocumentOut, ExtractionOut, ExtractionPatch, UploadResponse
from app.services import document_service as svc
from app.services.storage import get_storage

router = APIRouter(prefix="/documents", tags=["documents"])


async def _read_limited(file: UploadFile) -> bytes:
    limit = get_settings().max_upload_bytes
    data = await file.read(limit + 1)
    if len(data) > limit:
        raise AppError("FILE_TOO_LARGE", f"The file is larger than {get_settings().max_upload_mb} MB.", 413,
                       {"max_mb": get_settings().max_upload_mb})
    return data


@router.post("", response_model=UploadResponse, status_code=202, dependencies=[Depends(rate_limit("upload", 30))])  # API-01
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    doc_type: DocType = Form(DocType.LAB_REPORT),
    report_date: date | None = Form(None),
    category: ReportCategory | None = Form(None),
    description: str | None = Form(None, max_length=2000),
    owner: Owner = Depends(get_owner),
    db: Session = Depends(get_db),
):
    data = await _read_limited(file)
    doc = svc.create_document(db, owner, data, file.filename or "upload", doc_type, report_date,
                              category.value if category else None, description)
    svc.run_or_schedule(background_tasks, doc.id)
    db.refresh(doc)
    return UploadResponse(document_id=doc.id, status=doc.status)


@router.get("", response_model=DocumentList)  # API-11
def list_documents(
    type: DocType | None = None,
    category: str | None = None,
    lab: str | None = None,
    from_: date | None = Query(None, alias="from"),
    to: date | None = None,
    q: str | None = Query(None, max_length=200),
    limit: int = Query(100, le=500),
    offset: int = 0,
    owner: Owner = Depends(get_owner),
    db: Session = Depends(get_db),
):
    rows, total = svc.list_documents(db, owner, type, category, lab, from_, to, q, limit, offset)
    return DocumentList(items=[svc.to_out(db, d) for d in rows], total=total)


@router.get("/{document_id}", response_model=DocumentOut)  # API-02
def get_document(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    return svc.to_out(db, svc.get_owned(db, owner, document_id))


@router.get("/{document_id}/file")  # API-03
def get_file(document_id: uuid.UUID, download: bool = False, owner: Owner = Depends(get_owner),
             db: Session = Depends(get_db)):
    doc = svc.get_owned(db, owner, document_id)
    storage = get_storage()
    url = storage.signed_url(doc.storage_key, doc.original_filename)
    if url:
        return RedirectResponse(url, status_code=307)
    disposition = "attachment" if download else "inline"
    return Response(storage.get(doc.storage_key), media_type=doc.mime, headers={
        "Content-Disposition": f'{disposition}; filename="{doc.original_filename}"',
        "Cache-Control": "private, no-store",
    })


@router.get("/{document_id}/pages/{page_no}.png")  # page image for preview / verification crops
def get_page_image(document_id: uuid.UUID, page_no: int, owner: Owner = Depends(get_owner),
                   db: Session = Depends(get_db)):
    doc = svc.get_owned(db, owner, document_id)
    if page_no < 1 or page_no > doc.pages:
        raise AppError("NOT_FOUND", "Page not found.", 404)
    png = render_page_png(get_storage().get(doc.storage_key), doc.mime, page_no)
    return Response(png, media_type="image/png", headers={"Cache-Control": "private, max-age=300"})


@router.get("/{document_id}/extraction", response_model=ExtractionOut)  # API-04
def get_extraction(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    return svc.extraction_out(db, svc.get_owned(db, owner, document_id))


@router.patch("/{document_id}/extraction", response_model=ExtractionOut)  # API-05
def patch_extraction(document_id: uuid.UUID, patch: ExtractionPatch, owner: Owner = Depends(get_owner),
                     db: Session = Depends(get_db)):
    doc = svc.apply_extraction_patch(db, svc.get_owned(db, owner, document_id), patch)
    return svc.extraction_out(db, doc)


@router.post("/{document_id}/reprocess", response_model=UploadResponse, status_code=202)  # NFR-02 retry
def reprocess(document_id: uuid.UUID, background_tasks: BackgroundTasks, owner: Owner = Depends(get_owner),
              db: Session = Depends(get_db)):
    doc = svc.get_owned(db, owner, document_id)
    doc.status, doc.status_message = DocumentStatus.UPLOADED, None
    db.commit()
    svc.run_or_schedule(background_tasks, doc.id)
    db.refresh(doc)
    return UploadResponse(document_id=doc.id, status=doc.status)


@router.delete("/{document_id}", status_code=204)  # API-10
def delete_document(document_id: uuid.UUID, owner: Owner = Depends(get_owner), db: Session = Depends(get_db)):
    svc.delete_document(db, svc.get_owned(db, owner, document_id))
    return Response(status_code=204)
