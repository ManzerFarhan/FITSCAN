"""Confidence scoring & sanity checks (FR-LAB-7, FR-LAB-8, BR-02)."""
from __future__ import annotations

from app.pipelines.lab_report.range_parser import RefRange
from app.utils import dictionaries
from app.utils.units import convert, normalize_unit


def sanity_issues(
    parameter_id: str | None,
    value_num: float | None,
    value_raw: str | None,
    unit: str | None,
    ref: RefRange,
) -> list[str]:
    issues: list[str] = []
    if value_num is None:
        issues.append("MISSING_VALUE" if not value_raw else "NON_NUMERIC_VALUE")
    if parameter_id is None:
        issues.append("UNRECOGNIZED_PARAMETER")
    if not ref.parsed:
        issues.append("REFERENCE_RANGE_UNPARSED" if ref.raw else "REFERENCE_RANGE_MISSING")
    if parameter_id and value_num is not None:
        p = dictionaries.parameters()[parameter_id]
        v = value_num
        if unit and p.get("default_unit") and normalize_unit(unit) != p["default_unit"]:
            converted = convert(value_num, unit, p["default_unit"], parameter_id)
            v = converted if converted is not None else None
            if converted is None:
                issues.append("UNIT_UNRECOGNIZED")
        if v is not None:
            lo, hi = p.get("plausible_min"), p.get("plausible_max")
            if (lo is not None and v < lo) or (hi is not None and v > hi):
                issues.append("IMPLAUSIBLE_VALUE")
    if ref.parsed and ref.low is not None and ref.high is not None and value_num is not None:
        # A value 50x outside the lab's range is far more likely an OCR slip (e.g. lost decimal point)
        span = max(ref.high, 1e-9)
        if value_num > span * 50:
            issues.append("POSSIBLE_DECIMAL_ERROR")
    return issues


# Issues that force NEEDS_VERIFICATION regardless of OCR confidence.
BLOCKING_ISSUES = {
    "MISSING_VALUE", "NON_NUMERIC_VALUE", "UNRECOGNIZED_PARAMETER", "IMPLAUSIBLE_VALUE",
    "POSSIBLE_DECIMAL_ERROR", "AMBIGUOUS_ASSOCIATION",
}


def combine_confidence(ocr_conf: float, name_score: float, issues: list[str]) -> float:
    """Overall field confidence in [0,1]."""
    conf = min(ocr_conf, 1.0) * (0.5 + 0.5 * name_score)
    if any(i in BLOCKING_ISSUES for i in issues):
        conf = min(conf, 0.5)
    elif issues:
        conf *= 0.9
    return round(max(0.0, min(conf, 1.0)), 3)


def needs_verification(confidence: float, issues: list[str], threshold: float) -> bool:
    return confidence < threshold or any(i in BLOCKING_ISSUES for i in issues)
