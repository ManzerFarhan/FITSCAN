"""BR-05: OUT_OF_RANGE, UNCERTAIN and URGENT are distinct; URGENT only from escalation rules."""
from types import SimpleNamespace as NS

from app.services.findings import classify, is_urgent


def P(pid, value, unit, status, conf=0.99, issues=None, verified=True, flag=None):
    return NS(parameter_id=pid, value_num=value, unit=unit, status=status, confidence=conf, issues=issues or [],
              verified=verified, lab_flag=flag)


def test_out_of_range_is_not_urgent():
    assert classify(P("hemoglobin", 11.2, "g/dL", "BELOW")) == "OUT_OF_RANGE"


def test_urgent_only_via_rules_with_unit_conversion():
    assert classify(P("hemoglobin", 6.5, "g/dL", "BELOW")) == "URGENT"
    assert classify(P("platelet_count", 15000, "/cumm", "BELOW")) == "URGENT"       # 15 x10^3/µL < 20
    assert classify(P("platelet_count", 1.0, "lakhs/cumm", "BELOW")) == "OUT_OF_RANGE"  # 100 x10^3/µL
    assert classify(P("tsh", 50, "µIU/mL", "ABOVE")) == "OUT_OF_RANGE"              # no rule for TSH


def test_uncertain_wins_until_verified():
    p = P("hemoglobin", 6.5, "g/dL", "BELOW", conf=0.4, verified=False)
    assert classify(p) == "UNCERTAIN"
    p.verified = True
    assert classify(p) == "URGENT"


def test_unknown_unit_never_urgent():
    assert is_urgent("potassium", 9.0, "weird") is False


def test_within_range_has_no_finding():
    assert classify(P("hemoglobin", 13, "g/dL", "WITHIN")) is None
    assert classify(P("x", 1, None, "UNKNOWN", flag="H")) == "OUT_OF_RANGE"  # lab flag preserved as a finding
