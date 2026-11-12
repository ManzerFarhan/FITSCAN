"""Finding classes (BR-05): OUT_OF_RANGE, UNCERTAIN and URGENT are separate.

URGENT comes ONLY from config/escalation_rules.yaml - never from an LLM.
"""
from __future__ import annotations

from functools import lru_cache

import yaml

from app.core.config import get_settings
from app.core.constants import FindingClass, ParameterStatus
from app.pipelines.lab_report.confidence import needs_verification
from app.utils.units import convert


@lru_cache
def escalation_rules() -> dict[str, dict]:
    path = get_settings().config_dir / "escalation_rules.yaml"
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("rules", {})


def is_urgent(parameter_id: str | None, value: float | None, unit: str | None) -> bool:
    if not parameter_id or value is None:
        return False
    rule = escalation_rules().get(parameter_id)
    if not rule:
        return False
    v = convert(value, unit, rule["unit"], parameter_id) if unit else None
    if v is None:
        return False  # incompatible/unknown unit -> cannot apply a validated rule
    return ("low" in rule and v < rule["low"]) or ("high" in rule and v > rule["high"])


def param_needs_verification(p, threshold: float | None = None) -> bool:
    """`p` is a Parameter ORM row (or anything with the same attributes)."""
    if p.verified:
        return False
    t = threshold if threshold is not None else get_settings().confidence_threshold
    return needs_verification(p.confidence, p.issues or [], t)


def classify(p, threshold: float | None = None) -> str | None:
    if param_needs_verification(p, threshold):
        return FindingClass.UNCERTAIN
    if is_urgent(p.parameter_id, p.value_num, p.unit):
        return FindingClass.URGENT
    if p.status in (ParameterStatus.ABOVE, ParameterStatus.BELOW):
        return FindingClass.OUT_OF_RANGE
    if p.lab_flag and p.status == ParameterStatus.UNKNOWN:
        return FindingClass.OUT_OF_RANGE
    return None
