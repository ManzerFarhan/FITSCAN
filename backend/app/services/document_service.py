"""Document lifecycle: upload validation & storage, async pipeline orchestration, extraction
review/corrections, listing and deletion. (API-01..05, 10, 11; FR-UPL; FR-LAB-9). Printed lab reports only."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import Owner
from app.core.config import get_settings
from app.core.constants import (
    ALLOWED_EXTENSIONS,
    DocType,
    DocumentStatus,
    FindingClass,
    SourceTag,
)
from app.core.errors import AppError, not_found
from app.core.logging import get_logger
from app.db.models import Analysis, Document, ExtractionRun, Parameter
from app.db.session import SessionLocal
from app.pipelines.lab_report.pipeline import LabReportPipeline, build_parameter
from app.pipelines.preprocessing.pdf_loader import PageLimitExceeded, count_pdf_pages
from app.schemas.documents import DocumentOut, ExtractionOut, ExtractionPatch, MetadataFieldOut, ParameterOut
from app.services import audit, findings
from app.services.storage import get_storage
from app.utils import dictionaries

log = get_logger("documents")

_MAGIC = {
    "application/pdf": [b"%PDF"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/jpeg": [b"\xff\xd8\xff"],
}


def sniff_mime(data: bytes) -> str | None:
    for mime, sigs in _MAGIC.items():
        if any(data.startswith(s) for s in sigs):
            return mime
    return None


# ------------------------------------------------------------------ upload
def create_document(db: Session, owner: Owner, data: bytes, filename: str, doc_type: DocType,
                    report_date: date | None = None, category: str | None = None,
                    description: str | None = None) -> Document:
    s = get_settings()
    ext = Path(filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppError("UNSUPPORTED_FORMAT", "Only PDF, JPG, JPEG and PNG files are supported.", 415)
    if not data:
        raise AppError("EMPTY_FILE", "The file is empty.", 400)
    if len(data) > s.max_upload_bytes:
        raise AppError("FILE_TOO_LARGE", f"The file is larger than {s.max_upload_mb} MB.", 413,
                       {"max_mb": s.max_upload_mb})
    mime = sniff_mime(data)
    if mime is None or (ext == ".pdf") != (mime == "application/pdf"):
        raise AppError("UNSUPPORTED_FORMAT", "The file content does not match a PDF, JPG or PNG.", 415)
    pages = 1
    if mime == "application/pdf":
        try:
            pages = count_pdf_pages(data)
        except Exception:
            raise AppError("CORRUPT_FILE", "This PDF could not be opened. Is it password-protected or damaged?", 422)
        if pages > s.max_pdf_pages:
            raise AppError("TOO_MANY_PAGES", f"PDFs can have at most {s.max_pdf_pages} pages.", 413,
                           {"pages": pages, "max_pages": s.max_pdf_pages})

    doc_id = uuid.uuid4()
    key = f"documents/{owner.user_id or owner.guest_session_id}/{doc_id}{'.jpg' if mime == 'image/jpeg' else ext}"
    get_storage().put(key, data, mime)
    doc = Document(
        id=doc_id, doc_type=doc_type, original_filename=Path(filename).name[:255], storage_key=key, mime=mime,
        size_bytes=len(data), pages=pages, status=DocumentStatus.UPLOADED, report_date=report_date,
        report_category=category, description=description,
    )
    owner.stamp(doc)
    db.add(doc)
    db.flush()
    audit.record(db, owner, 'UPLOAD', 'document', doc.id, f'Uploaded lab report: {doc.original_filename}')
    return doc


# ------------------------------------------------------------------ processing (async job)
def _set_status(document_id: uuid.UUID, status: str, message: str | None = None) -> None:
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc:
            doc.status = status
            doc.status_message = message
            db.commit()


_IN_PROGRESS = (DocumentStatus.UPLOADED, DocumentStatus.PREPROCESSING, DocumentStatus.OCR_RUNNING, DocumentStatus.EXTRACTING)


def fail_interrupted(db: Session, older_than_minutes: int = 15) -> int:
    """Reading jobs run in-process, so a document still 'in progress' long after upload was cut off by a restart
    (deploy, crash). Mark it FAILED with a clear message instead of leaving it spinning forever."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=older_than_minutes)
    stuck = db.scalars(select(Document).where(Document.status.in_(_IN_PROGRESS), Document.uploaded_at < cutoff)).all()
    for doc in stuck:
        doc.status = DocumentStatus.FAILED
        doc.status_message = "Reading was interrupted (the server restarted). Please upload the report again."
    db.commit()
    return len(stuck)


def _patient_sex(db: Session, doc: Document) -> str | None:
    if doc.user_id:
        from app.db.models import User

        u = db.get(User, doc.user_id)
        if u and u.gender and u.gender[:1].upper() in ("M", "F"):
            return u.gender[:1].upper()
    return None


def process_document(document_id: uuid.UUID) -> None:
    """Background job. Opens its own session; never raises (failures -> FAILED + friendly message)."""
    s = get_settings()
    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        data = get_storage().get(doc.storage_key)
        mime, sex = doc.mime, _patient_sex(db, doc)
    on_stage = lambda st: _set_status(document_id, st)  # noqa: E731
    started = datetime.now(timezone.utc)
    try:
        result = LabReportPipeline(s.confidence_threshold, s.max_pdf_pages, on_stage).run(data, mime, sex=sex)
    except PageLimitExceeded as exc:
        _set_status(document_id, DocumentStatus.FAILED, str(exc))
        return
    except Exception as exc:
        log.exception("Pipeline failed for document (%s)", type(exc).__name__)
        _set_status(document_id, DocumentStatus.FAILED,
                    "We couldn't read this document. Try a clearer photo or the original PDF, then retry.")
        return

    with SessionLocal() as db:
        doc = db.get(Document, document_id)
        if doc is None:
            return
        db.add(ExtractionRun(document_id=doc.id, engine=result.engine, version=result.version, started_at=started,
                             finished_at=datetime.now(timezone.utc),
                             raw_json=result.model_dump(mode="json", exclude={"regions"})))
        # Replace previous extraction (reprocess)
        for p in list(doc.parameters):
            db.delete(p)
        db.flush()
        doc.metadata_json = {k: v.model_dump() for k, v in result.metadata.items()}
        _store_lab(db, doc, result)
        label = 'Extraction finished - please review' if doc.status == DocumentStatus.NEEDS_VERIFICATION else 'Extraction finished'
        audit.record(db, doc, 'EXTRACTED', 'document', doc.id, f'{label}: {doc.original_filename}', commit=False)
        db.commit()


def _apply_meta(doc: Document, meta: dict) -> None:
    def v(key):
        return (meta.get(key) or {}).get("value")

    doc.lab_name = doc.lab_name or v("lab_name")
    doc.lab_address = doc.lab_address or v("lab_address")
    doc.patient_name = doc.patient_name or v("patient_name")
    doc.patient_address = doc.patient_address or v("patient_address")
    doc.report_number = doc.report_number or v("report_number")
    doc.doctor_name = doc.doctor_name or v("doctor_name")
    doc.report_category = doc.report_category or v("report_category")
    for field, key in (("report_date", "report_date"), ("collected_date", "collected_date")):
        if getattr(doc, field) is None and v(key):
            setattr(doc, field, date.fromisoformat(v(key)))


def _store_lab(db: Session, doc: Document, result) -> None:
    _apply_meta(doc, doc.metadata_json or {})
    for ep in result.parameters:
        p = Parameter(
            document_id=doc.id, position=ep.position, parameter_id=ep.parameter_id, name_raw=ep.name_raw[:255],
            value_num=ep.value_num, value_raw=ep.value_raw, unit=ep.unit, unit_normalized=ep.unit_normalized,
            ref_low=ep.ref_low, ref_high=ep.ref_high, ref_raw=ep.ref_raw, lab_flag=ep.lab_flag, status=ep.status,
            confidence=ep.confidence, issues=ep.issues, bbox_json=ep.bbox.model_dump() if ep.bbox else None,
            page_no=ep.page_no, verified=False, source_tag=SourceTag.EXTRACTED,
        )
        p.finding_class = findings.classify(p)
        db.add(p)
    needs = result.needs_verification or any(
        (m.get("confidence", 0) < get_settings().confidence_threshold) for k, m in (doc.metadata_json or {}).items()
        if k in ("report_date",)
    )
    doc.status = DocumentStatus.NEEDS_VERIFICATION if needs else DocumentStatus.EXTRACTED
    doc.status_message = "No lab values were found. You can add them manually." if not result.parameters else None


def run_or_schedule(background_tasks, document_id: uuid.UUID) -> None:
    if get_settings().process_inline:
        process_document(document_id)
    else:
        background_tasks.add_task(process_document, document_id)


# ------------------------------------------------------------------ queries
def get_owned(db: Session, owner: Owner, document_id: uuid.UUID) -> Document:
    doc = db.get(Document, document_id)
    if doc is None or not owner.owns(doc):  # NFR-04: other owners' docs are indistinguishable from missing
        raise not_found("Document")
    return doc


def to_out(db: Session, doc: Document) -> DocumentOut:
    out = DocumentOut.model_validate(doc)
    params = doc.parameters
    out.parameter_count = len(params)
    out.out_of_range_count = sum(1 for p in params if p.finding_class in (FindingClass.OUT_OF_RANGE, FindingClass.URGENT))
    out.needs_verification_count = sum(1 for p in params if findings.param_needs_verification(p))
    out.has_analysis = db.scalar(select(func.count()).select_from(Analysis).where(Analysis.document_id == doc.id)) > 0
    return out


def _param_out(p: Parameter) -> ParameterOut:
    out = ParameterOut.model_validate(p)
    meta = dictionaries.parameters().get(p.parameter_id or "")
    out.canonical_name = meta["canonical_name"] if meta else None
    out.issues = p.issues or []
    out.needs_verification = findings.param_needs_verification(p)
    return out


def extraction_out(db: Session, doc: Document) -> ExtractionOut:
    run = db.scalar(select(ExtractionRun).where(ExtractionRun.document_id == doc.id).order_by(ExtractionRun.started_at.desc()))
    return ExtractionOut(
        document=to_out(db, doc),
        metadata={k: MetadataFieldOut(**v) for k, v in (doc.metadata_json or {}).items()},
        parameters=[_param_out(p) for p in doc.parameters],
        confidence_threshold=get_settings().confidence_threshold,
        warnings=(run.raw_json or {}).get("warnings", []) if run else [],
        engine=run.engine if run else None,
    )


def list_documents(db: Session, owner: Owner, doc_type: str | None = None, category: str | None = None,
                   lab: str | None = None, date_from: date | None = None, date_to: date | None = None,
                   q: str | None = None, limit: int = 100, offset: int = 0) -> tuple[list[Document], int]:
    stmt: Select = owner.scope(select(Document), Document)
    if doc_type:
        stmt = stmt.where(Document.doc_type == doc_type)
    if category:
        stmt = stmt.where(Document.report_category == category)
    if lab:
        stmt = stmt.where(Document.lab_name.ilike(f"%{lab}%"))
    eff_date = func.coalesce(Document.report_date, func.date(Document.uploaded_at))
    if date_from:
        stmt = stmt.where(eff_date >= date_from)
    if date_to:
        stmt = stmt.where(eff_date <= date_to)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Document.original_filename.ilike(like), Document.lab_name.ilike(like),
                              Document.description.ilike(like), Document.doctor_name.ilike(like)))
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(stmt.order_by(eff_date.desc(), Document.uploaded_at.desc()).limit(limit).offset(offset)).all()
    return list(rows), total or 0


# ------------------------------------------------------------------ corrections / verification
def apply_extraction_patch(db: Session, doc: Document, patch: ExtractionPatch) -> Document:
    if doc.status in (DocumentStatus.UPLOADED, DocumentStatus.PREPROCESSING, DocumentStatus.OCR_RUNNING, DocumentStatus.EXTRACTING):
        raise AppError("STILL_PROCESSING", "The document is still being processed.", 409)
    s = get_settings()
    sex = None
    meta = doc.metadata_json or {}
    if "patient_sex" in meta:
        sex = meta["patient_sex"].get("value")
    sex = _patient_sex(db, doc) or sex

    if patch.metadata:
        for field, value in patch.metadata.model_dump(exclude_unset=True).items():
            setattr(doc, field, value)

    by_id = {p.id: p for p in doc.parameters}
    for pp in patch.parameters:
        p = by_id.get(pp.id)
        if p is None:
            raise AppError("NOT_FOUND", "Parameter not found on this document.", 404, {"id": str(pp.id)})
        if pp.delete:
            db.delete(p)
            continue
        changes = pp.model_dump(exclude_unset=True, exclude={"id", "delete", "verified"})
        if changes:
            ep = build_parameter(
                p.position, changes.get("name_raw", p.name_raw), changes.get("value_raw", p.value_raw),
                changes.get("unit", p.unit), changes.get("ref_raw", p.ref_raw), changes.get("lab_flag", p.lab_flag),
                1.0, None, p.page_no, s.confidence_threshold, sex=sex,
                parameter_id=changes.get("parameter_id", p.parameter_id if "name_raw" not in changes else None),
            )
            p.name_raw, p.parameter_id = ep.name_raw, ep.parameter_id
            p.value_raw, p.value_num, p.unit, p.unit_normalized = ep.value_raw, ep.value_num, ep.unit, ep.unit_normalized
            p.ref_raw, p.ref_low, p.ref_high, p.lab_flag = ep.ref_raw, ep.ref_low, ep.ref_high, ep.lab_flag
            p.status, p.issues, p.confidence = ep.status, ep.issues, ep.confidence
            p.source_tag = SourceTag.USER_CORRECTED
            p.verified = True if pp.verified is None else pp.verified  # editing = the user checked it
        elif pp.verified is not None:
            p.verified = pp.verified
        p.finding_class = findings.classify(p)

    for i, np_ in enumerate(patch.new_parameters):
        ep = build_parameter(len(by_id) + i, np_.name_raw, np_.value_raw, np_.unit, np_.ref_raw, None, 1.0, None, 1,
                             s.confidence_threshold, sex=sex, parameter_id=np_.parameter_id)
        p = Parameter(document_id=doc.id, position=ep.position, parameter_id=ep.parameter_id, name_raw=ep.name_raw,
                      value_num=ep.value_num, value_raw=ep.value_raw, unit=ep.unit, unit_normalized=ep.unit_normalized,
                      ref_low=ep.ref_low, ref_high=ep.ref_high, ref_raw=ep.ref_raw, lab_flag=None, status=ep.status,
                      confidence=1.0, issues=ep.issues, page_no=1, verified=True, source_tag=SourceTag.USER_CORRECTED)
        p.finding_class = findings.classify(p)
        db.add(p)

    db.flush()
    db.refresh(doc)

    if patch.confirm:
        if patch.auto_check:
            auto_check(db, doc, sex)
        _confirm(db, doc, allow_unchecked=patch.auto_check)
    db.commit()
    db.refresh(doc)
    return doc


# Issues that mean a value cannot be trusted without a person looking at it.
AUTO_REJECT_ISSUES = {"MISSING_VALUE", "NON_NUMERIC_VALUE", "UNRECOGNIZED_PARAMETER", "IMPLAUSIBLE_VALUE",
                      "POSSIBLE_DECIMAL_ERROR", "AMBIGUOUS_ASSOCIATION", "LIKELY_NOT_A_TEST", "UNIT_UNRECOGNIZED"}
AUTO_MIN_CONFIDENCE = 0.6
AUTO_NAME_SCORE = 0.95


def auto_check(db: Session, doc: Document, sex: str | None) -> dict[str, int]:
    """Check flagged values automatically (user asked FITSCAN to do it).

    1. An unrecognised name with one clear dictionary match (>= 95 %) is matched to that test and re-evaluated.
    2. A value is accepted only if it passes every automated check: known test, numeric, plausible, unit understood,
       no decimal-slip or column-mix-up warning, and reasonable read confidence.
    3. Anything else stays unverified: the AI analysis leaves it out and lists it as excluded (BR-02).
    """
    from app.services.assistant_service import suggest_parameters

    s = get_settings()
    matched = accepted = left_out = 0
    for p in doc.parameters:
        if not findings.param_needs_verification(p):
            continue
        if p.parameter_id is None:
            sug = suggest_parameters(p.name_raw, limit=2)
            if sug and sug[0].score >= AUTO_NAME_SCORE and (len(sug) == 1 or sug[1].score < sug[0].score):
                ep = build_parameter(p.position, p.name_raw, p.value_raw, p.unit, p.ref_raw, p.lab_flag, p.confidence,
                                     None, p.page_no, s.confidence_threshold, sex=sex, parameter_id=sug[0].parameter_id)
                p.parameter_id, p.status, p.issues = ep.parameter_id, ep.status, ep.issues
                p.ref_low, p.ref_high, p.unit_normalized = ep.ref_low, ep.ref_high, ep.unit_normalized
                matched += 1
        issues = set(p.issues or [])
        if p.parameter_id and p.value_num is not None and not (issues & AUTO_REJECT_ISSUES) \
                and (p.confidence or 0) >= AUTO_MIN_CONFIDENCE:
            p.verified = True
            accepted += 1
        else:
            left_out += 1
        p.finding_class = findings.classify(p)
    audit.record(db, doc, "AUTO_CHECK", "document", doc.id,
                 f"Auto-check: {accepted} accepted, {left_out} left out, {matched} names matched", commit=False)
    return {"accepted": accepted, "left_out": left_out, "matched": matched}


def _confirm(db: Session, doc: Document, allow_unchecked: bool = False) -> None:
    """User confirms the reviewed extraction. Flagged fields must have been checked individually, unless the user
    chose auto-check - then values that are still doubtful simply stay unverified and are excluded from analysis."""
    if doc.report_date is None:  # BR-14: the actual report date is required (never the upload date)
        raise AppError("REPORT_DATE_REQUIRED", "Please add the date printed on the report before confirming.", 409)
    pending = [str(p.id) for p in doc.parameters if findings.param_needs_verification(p)]
    if pending and not allow_unchecked:
        raise AppError("PENDING_VERIFICATION", "Please check every highlighted value before confirming.", 409,
                       {"parameter_ids": pending})
    for p in doc.parameters:
        if not findings.param_needs_verification(p):
            p.verified = True
        p.finding_class = findings.classify(p)
    doc.status = DocumentStatus.VERIFIED
    audit.record(db, doc, 'VERIFIED', 'document', doc.id, f'Confirmed extracted data: {doc.original_filename}', commit=False)


# ------------------------------------------------------------------ delete
def delete_document(db: Session, doc: Document) -> None:
    key = doc.storage_key
    db.delete(doc)  # parameters, analyses and chats cascade
    db.commit()
    try:
        get_storage().delete(key)
    except Exception:
        log.warning("Storage object could not be deleted; will be retried by retention job")
