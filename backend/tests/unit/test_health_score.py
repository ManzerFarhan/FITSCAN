"""Dashboard health score and BMI (synthetic values only; BR-01/02/04/05)."""
import uuid
from datetime import UTC, date, datetime

import pytest

from app.db.models import Document, Parameter
from app.services import health_score as hs


def P(status, value=None, lo=None, hi=None, verified=True, finding=None):
    return Parameter(id=uuid.uuid4(), name_raw="t", status=status, value_num=value, ref_low=lo, ref_high=hi,
                     verified=verified, finding_class=finding, source_tag="EXTRACTED")


def doc(params, day=1):
    d = Document(id=uuid.uuid4(), report_date=date(2025, 1, day), uploaded_at=datetime.now(UTC), lab_name="Lab")
    d.parameters = params
    return d


def test_all_within_scores_ten():
    s = hs.score_document(doc([P("WITHIN", 5, 1, 10)] * 4))
    assert s["score"] == 10.0 and s["within"] == 4 and hs.band(s["score"]) == "MOSTLY_WITHIN"


def test_slight_vs_well_outside_and_urgent():
    params = [
        P("WITHIN", 5, 1, 10),
        P("ABOVE", 11, 1, 10, finding="OUT_OF_RANGE"),    # 1 beyond a width of 9 -> slight
        P("BELOW", 5, 12, 16, finding="OUT_OF_RANGE"),    # 7 below a width of 4 -> well outside
        P("ABOVE", 400, None, 100, finding="URGENT"),     # escalation rule -> 0 points
    ]
    s = hs.score_document(doc(params))
    assert (s["within"], s["slightly_outside"], s["well_outside"], s["urgent"]) == (1, 1, 1, 1)
    assert s["score"] == round(10 * (1 + 0.6 + 0.3 + 0) / 4, 1)


def test_unverified_and_unknown_are_not_counted():  # BR-02 / BR-01
    params = [P("WITHIN", 5, 1, 10), P("WITHIN", 5, 1, 10), P("ABOVE", 50, 1, 10, verified=False), P("UNKNOWN", 3)]
    assert hs.score_document(doc(params)) is None  # only 2 scorable values
    out = hs.lab_score([doc(params)])
    assert out["available"] is False and "Confirm at least" in out["reason"]


def test_previous_report_score_is_reported():
    newer = doc([P("WITHIN", 5, 1, 10)] * 3, day=20)
    older = doc([P("WITHIN", 5, 1, 10)] * 2 + [P("ABOVE", 11, 1, 10)], day=2)
    out = hs.lab_score([newer, older])
    assert out["score"] == 10.0 and out["previous"]["score"] == round(10 * 2.6 / 3, 1)
    assert out["previous"]["report_date"] == "2025-01-02"


def test_no_reports():
    assert hs.lab_score([])["reason"].startswith("Upload a lab report")


@pytest.mark.parametrize("h,w,value,cat", [(170, 50, 17.3, "UNDERWEIGHT"), (170, 65, 22.5, "NORMAL"),
                                            (170, 80, 27.7, "OVERWEIGHT"), (170, 95, 32.9, "OBESE")])
def test_bmi(h, w, value, cat):
    assert hs.bmi(h, w) == {"value": value, "category": cat, "height_cm": h, "weight_kg": w}


def test_bmi_optional():
    assert hs.bmi(None, 70) is None and hs.bmi(170, None) is None
