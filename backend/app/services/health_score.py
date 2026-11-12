"""Dashboard "health score" out of 10 and BMI.

The lab score summarises how many VERIFIED results (BR-02) of a report fall inside the range printed by the lab
itself (BR-01), with a smaller credit for values just outside and none for values flagged URGENT by the escalation
rules (BR-05). It is a summary of the report, not a judgement about the person's health (BR-04), and comparisons
with an earlier report are shown neutrally (BR-09).
"""
from __future__ import annotations

from app.core.constants import BmiCategory, FindingClass, HealthScoreBand, ParameterStatus
from app.db.models import Document, Parameter

MIN_SCORED = 3            # fewer verified results with a printed range -> no score
SLIGHT_MARGIN = 0.25      # outside by <= 25 % of the range width (or of the limit) counts as "slightly outside"
POINTS = {"within": 1.0, "slightly_outside": 0.6, "well_outside": 0.3, "urgent": 0.0}

METHOD = ("Each confirmed result with a range printed by your lab earns points: inside the range 1, slightly outside "
          "0.6, well outside 0.3, flagged for prompt attention 0. The score is the average x 10. Results you have not "
          "confirmed, or without a printed range, are not counted.")


def _bucket(p: Parameter) -> str | None:
    if not p.verified or p.value_num is None or p.status not in (
            ParameterStatus.WITHIN, ParameterStatus.ABOVE, ParameterStatus.BELOW):
        return None
    if p.finding_class == FindingClass.URGENT:
        return "urgent"
    if p.status == ParameterStatus.WITHIN:
        return "within"
    lo, hi, v = p.ref_low, p.ref_high, p.value_num
    width = (hi - lo) if lo is not None and hi is not None and hi > lo else None
    if p.status == ParameterStatus.ABOVE and hi is not None:
        gap, scale = v - hi, width or abs(hi)
    elif p.status == ParameterStatus.BELOW and lo is not None:
        gap, scale = lo - v, width or abs(lo)
    else:  # lab flag without a numeric limit
        return "slightly_outside"
    if not scale:
        return "well_outside"
    return "slightly_outside" if gap / scale <= SLIGHT_MARGIN else "well_outside"


def band(score: float) -> HealthScoreBand:
    if score >= 8.5:
        return HealthScoreBand.MOSTLY_WITHIN
    return HealthScoreBand.SOME_OUTSIDE if score >= 6.0 else HealthScoreBand.MANY_OUTSIDE


def score_document(doc: Document) -> dict | None:
    counts = {k: 0 for k in POINTS}
    for p in doc.parameters:
        b = _bucket(p)
        if b:
            counts[b] += 1
    n = sum(counts.values())
    if n < MIN_SCORED:
        return None
    score = round(10 * sum(POINTS[k] * c for k, c in counts.items()) / n, 1)
    return {"score": score, "counted": n, **counts}


def lab_score(lab_docs: list[Document]) -> dict:
    """Score for the newest report that can be scored; `lab_docs` must be sorted newest first."""
    for i, d in enumerate(lab_docs):
        s = score_document(d)
        if s is None:
            continue
        prev = None
        for older in lab_docs[i + 1:]:
            ps = score_document(older)
            if ps:
                prev = {"score": ps["score"], "report_date": (older.report_date or older.uploaded_at.date()).isoformat(),
                        "document_id": str(older.id)}
                break
        return {
            "available": True, "out_of": 10, **s, "band": band(s["score"]).value,
            "excluded_unverified": sum(1 for p in d.parameters if not p.verified),
            "report_date": (d.report_date or d.uploaded_at.date()).isoformat(), "document_id": str(d.id),
            "lab_name": d.lab_name, "previous": prev, "method": METHOD,
        }
    reason = ("Upload a lab report to see your score." if not lab_docs else
              f"Confirm at least {MIN_SCORED} values that have a range printed by your lab to see your score.")
    return {"available": False, "out_of": 10, "reason": reason, "method": METHOD}


def bmi(height_cm: float | None, weight_kg: float | None) -> dict | None:
    """WHO adult BMI. Height and weight are optional profile fields entered by the user."""
    if not height_cm or not weight_kg:
        return None
    value = round(weight_kg / (height_cm / 100) ** 2, 1)
    cat = (BmiCategory.UNDERWEIGHT if value < 18.5 else BmiCategory.NORMAL if value < 25
           else BmiCategory.OVERWEIGHT if value < 30 else BmiCategory.OBESE)
    return {"value": value, "category": cat.value, "height_cm": height_cm, "weight_kg": weight_kg}
