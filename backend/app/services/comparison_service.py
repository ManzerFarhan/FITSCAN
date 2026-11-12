"""Historical comparison (FR-HIST-3..5, BR-02, BR-09; P3-23, P3-27).

Only VERIFIED parameters with a canonical parameter_id are compared; values are converted to a common
unit when the units are compatible, otherwise listed as non-comparable. Language is purely numeric /
directional - never improved/worsened.
"""
from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.db.models import Comparison, Document
from app.rag import prompts
from app.rag.llm_client import get_llm, parse_json
from app.rag.safety_validator import generate_safely
from app.services import audit
from app.services.document_service import get_owned
from app.utils import dictionaries
from app.utils.units import conversion_factor, normalize_unit

REL_TOL = 1e-6


def _eff_date(d: Document) -> date:
    return d.report_date or d.uploaded_at.date()


def _name(pid: str) -> str:
    return dictionaries.parameters().get(pid, {}).get("canonical_name", pid)


def _direction(prev: float, cur: float) -> str:
    if abs(cur - prev) <= REL_TOL * max(abs(prev), 1.0):
        return "unchanged"
    return "higher" if cur > prev else "lower"


def _out(status: str) -> bool:
    return status in ("ABOVE", "BELOW")


def compute(docs: list[Document]) -> dict:
    """Pure comparison over already-loaded documents (sorted oldest -> newest)."""
    docs = sorted(docs, key=lambda d: (_eff_date(d), d.uploaded_at))
    by_pid: dict[str, list[tuple[Document, object]]] = {}
    excluded_unverified = 0
    unrecognized = []
    for d in docs:
        for p in d.parameters:
            if not p.verified:
                excluded_unverified += 1
                continue
            if not p.parameter_id or p.value_num is None:
                unrecognized.append({"name": p.name_raw, "document_id": str(d.id), "date": _eff_date(d).isoformat(),
                                     "reason": "Not recognised as a standard parameter or value is not numeric"})
                continue
            by_pid.setdefault(p.parameter_id, []).append((d, p))

    compared, unmatched, non_comparable = [], [], []
    for pid, entries in by_pid.items():
        if len({d.id for d, _ in entries}) < 2:
            d, p = entries[0]
            unmatched.append({"parameter_id": pid, "name": _name(pid), "document_id": str(d.id),
                              "date": _eff_date(d).isoformat(), "reason": "Only present in one selected report"})
            continue
        target_unit = entries[-1][1].unit
        points, incompatible = [], []
        for d, p in entries:
            f = conversion_factor(p.unit, target_unit, pid) if (p.unit or target_unit) else 1.0
            if f is None:
                incompatible.append(p.unit)
                continue
            points.append({
                "document_id": str(d.id), "date": _eff_date(d).isoformat(), "lab_name": d.lab_name,
                "value": round(p.value_num * f, 4), "value_raw": p.value_raw, "unit_raw": p.unit,
                "ref_low": round(p.ref_low * f, 4) if p.ref_low is not None else None,
                "ref_high": round(p.ref_high * f, 4) if p.ref_high is not None else None,
                "ref_raw": p.ref_raw, "status": p.status, "converted": f != 1.0,
            })
        if incompatible:
            non_comparable.append({"parameter_id": pid, "name": _name(pid),
                                   "reason": f"Units cannot be converted reliably ({', '.join(sorted({str(u) for u in incompatible + [target_unit]}))})"})
            if len(points) < 2:
                continue
        prev, cur = points[-2], points[-1]
        first = points[0]
        abs_change = round(cur["value"] - prev["value"], 4)
        pct = round(abs_change / prev["value"] * 100, 1) if abs(prev["value"]) > 1e-9 else None
        range_changed = (prev["ref_low"], prev["ref_high"]) != (cur["ref_low"], cur["ref_high"])
        if not _out(prev["status"]) and _out(cur["status"]):
            transition = "NEWLY_OUTSIDE_RANGE"
        elif _out(prev["status"]) and cur["status"] == "WITHIN":
            transition = "NEWLY_INSIDE_RANGE"
        elif _out(prev["status"]) and _out(cur["status"]):
            transition = "STILL_OUTSIDE_RANGE"
        else:
            transition = "NO_RANGE_CHANGE"
        compared.append({
            "parameter_id": pid, "name": _name(pid), "category": dictionaries.parameters().get(pid, {}).get("category"),
            "unit": normalize_unit(target_unit) or target_unit, "points": points,
            "previous": prev, "current": cur, "absolute_change": abs_change, "percent_change": pct,
            "overall_change": round(cur["value"] - first["value"], 4), "direction": _direction(prev["value"], cur["value"]),
            "reference_range_changed": range_changed, "transition": transition,
        })
    compared.sort(key=lambda c: (c["category"] or "", c["name"]))
    return {
        "documents": [{"document_id": str(d.id), "date": _eff_date(d).isoformat(), "lab_name": d.lab_name,
                       "category": d.report_category, "filename": d.original_filename} for d in docs],
        "compared": compared, "unmatched": unmatched + unrecognized, "non_comparable": non_comparable,
        "excluded_unverified": excluded_unverified,
    }


def _fmt(v: float) -> str:
    return f"{v:g}"


def template_summary(result: dict) -> tuple[str, list[str]]:
    lines = []
    changed = [c for c in result["compared"] if c["direction"] != "unchanged"]
    if changed:
        bits = []
        for c in changed[:6]:
            pct = f", {abs(c['percent_change'])}%" if c["percent_change"] is not None else ""
            bits.append(f"{c['name']} is {c['direction']} ({_fmt(c['previous']['value'])} -> {_fmt(c['current']['value'])} {c['unit'] or ''}{pct})")
        lines.append("Compared with the previous report: " + "; ".join(bits) + ".")
    elif result["compared"]:
        lines.append("The matched values are unchanged between the two most recent reports.")
    for key, label in (("STILL_OUTSIDE_RANGE", "Still outside the lab's range"),
                       ("NEWLY_OUTSIDE_RANGE", "Newly outside the lab's range"),
                       ("NEWLY_INSIDE_RANGE", "Moved inside the lab's range")):
        names = [c["name"] for c in result["compared"] if c["transition"] == key]
        if names:
            lines.append(f"{label}: {', '.join(names)}.")
    rc = [c["name"] for c in result["compared"] if c["reference_range_changed"]]
    if rc:
        lines.append(f"The lab's reference range differs between reports for: {', '.join(rc)} - keep this in mind when reading changes.")
    nc = [x["name"] for x in result["non_comparable"]] + [x["name"] for x in result["unmatched"]]
    if nc:
        lines.append(f"Not compared: {', '.join(sorted(set(nc))[:8])}.")
    if result["excluded_unverified"]:
        lines.append(f"{result['excluded_unverified']} unverified value(s) were left out.")
    qs = [f"What might explain the change in my {c['name']}?" for c in changed[:2]]
    qs += ["Are these changes meaningful for me, given my history?", "How often should these values be reviewed?"]
    return " ".join(lines) or "No values could be matched between these reports.", qs[:5]


def create(db: Session, owner, document_ids: list[uuid.UUID]) -> Comparison:
    ids = list(dict.fromkeys(document_ids))
    if len(ids) < 2:
        raise AppError("VALIDATION_ERROR", "Choose at least two reports to compare.", 422)
    docs = [get_owned(db, owner, i) for i in ids]
    result = compute(docs)
    summary, questions = template_summary(result)
    generated_by = "fitscan-template"
    llm = get_llm()
    if llm.available and result["compared"]:
        def gen(feedback):
            msgs = [{"role": "user", "content": prompts.comparison_prompt({k: result[k] for k in ("compared", "non_comparable", "unmatched")})}]
            if feedback:
                msgs.append({"role": "user", "content": prompts.regenerate_feedback(feedback)})
            return llm.complete(prompts.SYSTEM_RULES, msgs, max_tokens=3000, json_schema=prompts.COMPARISON_SCHEMA)

        def extract(raw):
            try:
                d = parse_json(raw)
                return d["summary"] + "\n" + "\n".join(d["doctor_questions"])
            except Exception:
                return raw

        raw, used = generate_safely(gen, lambda: "", "comparison", extract=extract)
        if used:
            try:
                d = parse_json(raw)
                summary, questions, generated_by = d["summary"], d["doctor_questions"][:5], llm.name
            except Exception:
                pass
    result["summary"] = {"text": summary, "doctor_questions": questions, "generated_by": generated_by,
                         "source_tag": "AI_GENERATED"}
    comp = Comparison(document_ids=[str(i) for i in ids], result_json=result, summary_text=summary)
    owner.stamp(comp)
    db.add(comp)
    audit.record(db, owner, "COMPARISON", "comparison", None, f"Compared {len(ids)} reports", commit=False)
    db.commit()
    db.refresh(comp)
    return comp
