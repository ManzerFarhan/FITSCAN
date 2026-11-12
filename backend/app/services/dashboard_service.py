"""Dashboard aggregation (API-15, FR-DASH-3..7)."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import Owner
from app.core.constants import DocumentStatus, FindingClass
from app.db.models import Document, Parameter
from app.services import document_service, health_score
from app.utils import dictionaries

_FINDING_ORDER = {FindingClass.URGENT: 0, FindingClass.OUT_OF_RANGE: 1, FindingClass.UNCERTAIN: 2}


def _eff_date(d: Document):
    return d.report_date or d.uploaded_at.date()


def _previous_value(db: Session, owner: Owner, doc: Document, p: Parameter) -> dict | None:
    """Change vs the most recent EARLIER report with the same verified parameter (BR-02, BR-09)."""
    if not p.parameter_id or not p.verified or p.value_num is None:
        return None
    stmt = owner.scope(select(Parameter, Document).join(Document, Parameter.document_id == Document.id), Document) \
        .where(Parameter.parameter_id == p.parameter_id, Parameter.verified.is_(True), Document.id != doc.id,
               Parameter.value_num.is_not(None))
    best = None
    for prev_p, prev_d in db.execute(stmt).all():
        if _eff_date(prev_d) < _eff_date(doc) and (best is None or _eff_date(prev_d) > _eff_date(best[1])):
            best = (prev_p, prev_d)
    if not best:
        return None
    from app.utils.units import convert

    prev_p, prev_d = best
    v = convert(prev_p.value_num, prev_p.unit, p.unit, p.parameter_id) if prev_p.unit and p.unit else (
        prev_p.value_num if prev_p.unit == p.unit else None)
    if v is None:
        return None
    return {"value": round(v, 4), "date": _eff_date(prev_d).isoformat(), "document_id": str(prev_d.id),
            "change": round(p.value_num - v, 4)}


_STATUSES = ("WITHIN", "BELOW", "ABOVE", "UNKNOWN")


def _charts(lab_docs: list[Document]) -> dict:
    """Chart data for the dashboard. Uses the lab's own status per value (BR-01); trends use verified values only (BR-02)."""
    from app.utils.units import convert

    latest_status = None
    if lab_docs:
        d = lab_docs[0]
        latest_status = {s.lower(): sum(1 for p in d.parameters if p.status == s) for s in _STATUSES}
        latest_status["needs_check"] = sum(1 for p in d.parameters if not p.verified)

    # Latest result per test (newest report first), grouped by body system.
    latest_per_param: dict[str, Parameter] = {}
    for d in lab_docs:
        for p in d.parameters:
            key = p.parameter_id or p.name_raw.lower()
            latest_per_param.setdefault(key, p)
    systems: dict[str, dict] = {}
    for key, p in latest_per_param.items():
        meta = dictionaries.parameters().get(p.parameter_id or "")
        cat = meta["category"] if meta else "OTHER"
        row = systems.setdefault(cat, {"category": cat, "within": 0, "outside": 0, "unknown": 0})
        row["outside" if p.status in ("ABOVE", "BELOW") else "within" if p.status == "WITHIN" else "unknown"] += 1
    by_system = sorted(systems.values(), key=lambda r: (-r["outside"], -(r["within"] + r["outside"] + r["unknown"])))

    # Value over time for each verified test, in the newest report's unit.
    series: dict[str, dict] = {}
    for d in lab_docs:  # newest first -> the first hit sets unit and range
        for p in d.parameters:
            if not (p.parameter_id and p.verified and p.value_num is not None):
                continue
            s = series.get(p.parameter_id)
            if s is None:
                meta = dictionaries.parameters().get(p.parameter_id)
                s = series[p.parameter_id] = {
                    "parameter_id": p.parameter_id, "name": meta["canonical_name"] if meta else p.name_raw,
                    "unit": p.unit, "ref_low": p.ref_low, "ref_high": p.ref_high, "latest_status": p.status, "points": []}
                v = p.value_num
            elif p.unit == s["unit"]:
                v = p.value_num
            else:
                v = convert(p.value_num, p.unit, s["unit"], p.parameter_id) if p.unit and s["unit"] else None
            if v is not None:
                s["points"].append({"date": _eff_date(d).isoformat(), "value": round(v, 4), "status": p.status,
                                    "document_id": str(d.id)})
    trends = list(series.values())
    for s in trends:
        s["points"].sort(key=lambda x: x["date"])
    trends.sort(key=lambda s: (-len(s["points"]), s["latest_status"] not in ("ABOVE", "BELOW"), s["name"]))
    return {"latest_status": latest_status, "by_system": by_system, "trends": trends[:15]}


def build(db: Session, owner: Owner) -> dict:
    docs = db.scalars(owner.scope(select(Document), Document)).all()
    lab_docs = sorted(docs, key=lambda d: (_eff_date(d), d.uploaded_at), reverse=True)

    params = [p for d in lab_docs for p in d.parameters]
    findings = []
    for d in lab_docs:
        for p in d.parameters:
            if not p.finding_class:
                continue
            meta = dictionaries.parameters().get(p.parameter_id or "")
            findings.append({
                "document_id": str(d.id), "parameter_row_id": str(p.id), "parameter_id": p.parameter_id,
                "name": meta["canonical_name"] if meta else p.name_raw, "value": p.value_raw, "unit": p.unit,
                "ref_raw": p.ref_raw, "status": p.status, "lab_flag": p.lab_flag, "finding_class": p.finding_class,
                "verified": p.verified, "report_date": _eff_date(d).isoformat(), "lab_name": d.lab_name,
                "previous": _previous_value(db, owner, d, p),
            })
    findings.sort(key=lambda f: (_FINDING_ORDER.get(f["finding_class"], 9), f["report_date"]), reverse=False)

    latest = None
    if lab_docs:
        d = lab_docs[0]
        out = document_service.to_out(db, d).model_dump(mode="json")
        within = sum(1 for p in d.parameters if p.status == "WITHIN")
        out["summary"] = (f"{len(d.parameters)} parameters extracted: {within} within the lab's range, "
                          f"{out['out_of_range_count']} outside it, {out['needs_verification_count']} need your check.")
        latest = out

    to_review = sum(1 for d in docs if d.status in (DocumentStatus.NEEDS_VERIFICATION, DocumentStatus.EXTRACTED))
    return {
        "user": {"full_name": owner.user.full_name if owner.user else None, "is_guest": owner.is_guest},
        "cards": {
            "total_reports": len(docs),
            "tests_analyzed": len(params),
            "out_of_range": sum(1 for p in params if p.finding_class in (FindingClass.OUT_OF_RANGE, FindingClass.URGENT)),
            "to_review": to_review,
        },
        "latest_report": latest,
        "important_findings": findings[:20],
        "charts": _charts(lab_docs),
        "health_score": health_score.lab_score(lab_docs) if owner.user else None,  # log in to unlock
        "bmi": health_score.bmi(owner.user.height_cm, owner.user.weight_kg) if owner.user else None,
    }
