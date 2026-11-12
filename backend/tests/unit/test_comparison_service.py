"""BR-09 / FR-HIST-3: comparison numerics on synthetic data (100% numerical consistency target)."""
import uuid
from datetime import date, datetime, timezone
from types import SimpleNamespace as NS

import pytest

from app.rag.safety_validator import validate
from app.services.comparison_service import compute, template_summary


def P(pid, value, unit, lo=None, hi=None, status="WITHIN", verified=True, ref=None):
    return NS(parameter_id=pid, value_num=value, value_raw=str(value), unit=unit, ref_low=lo, ref_high=hi,
              ref_raw=ref or f"{lo}-{hi}", status=status, verified=verified, name_raw=pid)


def D(d, params, lab="Lab A"):
    return NS(id=uuid.uuid4(), report_date=d, uploaded_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
              lab_name=lab, report_category="LIPID", original_filename="x.pdf", parameters=params)


def test_deltas_and_percent():
    old = D(date(2024, 1, 1), [P("ldl", 160, "mg/dL", None, 100, "ABOVE")])
    new = D(date(2024, 6, 1), [P("ldl", 120, "mg/dL", None, 100, "ABOVE")])
    r = compute([new, old])  # order of input must not matter
    c = r["compared"][0]
    assert c["previous"]["value"] == 160 and c["current"]["value"] == 120
    assert c["absolute_change"] == -40
    assert c["percent_change"] == pytest.approx(-25.0)
    assert c["direction"] == "lower"
    assert c["transition"] == "STILL_OUTSIDE_RANGE"


def test_unit_normalization_mmol_to_mgdl():
    old = D(date(2024, 1, 1), [P("glucose_fasting", 5.5, "mmol/L", 3.9, 5.6)])
    new = D(date(2024, 6, 1), [P("glucose_fasting", 110, "mg/dL", 70, 100, "ABOVE")])
    c = compute([old, new])["compared"][0]
    assert c["previous"]["value"] == pytest.approx(99.088, rel=1e-3)
    assert c["previous"]["converted"] is True
    assert c["transition"] == "NEWLY_OUTSIDE_RANGE"
    assert c["unit"] == "mg/dL"


def test_incompatible_units_not_compared():
    old = D(date(2024, 1, 1), [P("hba1c", 6.0, "%")])
    new = D(date(2024, 6, 1), [P("hba1c", 42, "mmol/mol")])
    r = compute([old, new])
    assert r["compared"] == []
    assert r["non_comparable"][0]["parameter_id"] == "hba1c"


def test_zero_baseline_has_no_percent():
    old = D(date(2024, 1, 1), [P("basophils_pct", 0, "%", 0, 1)])
    new = D(date(2024, 6, 1), [P("basophils_pct", 1, "%", 0, 1)])
    assert compute([old, new])["compared"][0]["percent_change"] is None


def test_unverified_excluded_and_unmatched_listed():  # BR-02
    old = D(date(2024, 1, 1), [P("hdl", 40, "mg/dL", 40, 60), P("tsh", 2, "µIU/mL", verified=False)])
    new = D(date(2024, 6, 1), [P("hdl", 45, "mg/dL", 40, 60), P("tsh", 9, "µIU/mL", 0.4, 4, "ABOVE"), P("vitamin_d", 20, "ng/mL")])
    r = compute([old, new])
    assert r["excluded_unverified"] == 1
    assert {u["parameter_id"] for u in r["unmatched"] if "parameter_id" in u} == {"tsh", "vitamin_d"}


def test_reference_range_change_flagged():
    old = D(date(2024, 1, 1), [P("hemoglobin", 13, "g/dL", 12, 15)])
    new = D(date(2024, 6, 1), [P("hemoglobin", 13, "g/dL", 13, 17)], lab="Lab B")
    c = compute([old, new])["compared"][0]
    assert c["reference_range_changed"] is True and c["direction"] == "unchanged"


def test_summary_has_no_judgement_language():  # BR-09
    old = D(date(2024, 1, 1), [P("ldl", 160, "mg/dL", None, 100, "ABOVE"), P("hdl", 35, "mg/dL", 40, None, "BELOW")])
    new = D(date(2024, 6, 1), [P("ldl", 95, "mg/dL", None, 100, "WITHIN"), P("hdl", 42, "mg/dL", 40, None, "WITHIN")])
    text, qs = template_summary(compute([old, new]))
    assert "Moved inside the lab's range" in text
    assert validate(text + " ".join(qs), "comparison").ok
