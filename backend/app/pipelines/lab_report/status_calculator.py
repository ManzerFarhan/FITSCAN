"""Parameter status from the report's OWN reference range (FR-LAB-10, BR-01)."""
from app.core.constants import ParameterStatus
from app.pipelines.lab_report.range_parser import RefRange

_FLAG_MAP = {
    "H": "H", "HIGH": "H", "HH": "HH", "*H": "H", "H*": "H", "↑": "H",
    "L": "L", "LOW": "L", "LL": "LL", "*L": "L", "L*": "L", "↓": "L",
    "*": "*", "**": "*", "A": "*", "ABNORMAL": "*",
}


def normalize_lab_flag(raw: str | None) -> str | None:
    """Preserve lab flags (FR-LAB-11) in a canonical spelling: H, L, HH, LL, *."""
    if not raw:
        return None
    return _FLAG_MAP.get(raw.strip().upper())


def compute_status(value: float | None, ref: RefRange | None) -> ParameterStatus:
    if value is None or ref is None or not ref.parsed:
        return ParameterStatus.UNKNOWN
    if ref.low is not None:
        if value < ref.low or (not ref.low_inclusive and value == ref.low):
            return ParameterStatus.BELOW
    if ref.high is not None:
        if value > ref.high or (not ref.high_inclusive and value == ref.high):
            return ParameterStatus.ABOVE
    return ParameterStatus.WITHIN
