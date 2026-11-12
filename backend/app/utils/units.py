"""Unit normalization and conversion (FR-HIST-3, P2-03)."""
from __future__ import annotations

import re

from app.utils import dictionaries


def _alias_key(unit: str) -> str:
    u = unit.strip().lower().replace("μ", "µ").replace("³", "^3")
    u = re.sub(r"\s+", " ", u)
    u = re.sub(r"\s*/\s*", "/", u)
    return u


def normalize_unit(raw: str | None) -> str | None:
    """Map a raw unit string to its canonical spelling. Unknown units are returned trimmed."""
    if raw is None:
        return None
    raw = raw.strip()
    if not raw:
        return None
    aliases = dictionaries.unit_conversions()["aliases"]
    key = _alias_key(raw)
    for candidate in (key, key.replace(" ", ""), key.replace("µ", "u")):
        if candidate in aliases:
            return aliases[candidate]
    # Already canonical (e.g. "g/dL")?
    canon = set(aliases.values())
    return raw if raw in canon else raw


def _group_for(parameter_id: str | None) -> str | None:
    if not parameter_id:
        return None
    conv = dictionaries.unit_conversions()
    extra = conv.get("parameter_groups_extra", {})
    if parameter_id in extra:
        return extra[parameter_id]
    p = dictionaries.parameters().get(parameter_id)
    return p.get("conversion_group") if p else None


def _rules(parameter_id: str | None) -> list[dict]:
    conv = dictionaries.unit_conversions()
    rules = list(conv["generic"])
    group = _group_for(parameter_id)
    if group:
        rules = conv["group_specific"].get(group, []) + rules
    return rules


def conversion_factor(from_unit: str | None, to_unit: str | None, parameter_id: str | None = None) -> float | None:
    """Factor f such that value_to = value_from * f, or None if units are not compatible."""
    a, b = normalize_unit(from_unit), normalize_unit(to_unit)
    if a is None or b is None:
        return None
    if a == b:
        return 1.0
    rules = _rules(parameter_id)
    # direct / reverse
    for r in rules:
        if r["from"] == a and r["to"] == b:
            return r["factor"]
        if r["from"] == b and r["to"] == a:
            return 1.0 / r["factor"]
    # one hop through an intermediate unit
    for r1 in rules:
        for mid, f1 in ((r1["to"], r1["factor"]), (r1["from"], 1.0 / r1["factor"])):
            src = r1["from"] if mid == r1["to"] else r1["to"]
            if src != a:
                continue
            for r2 in rules:
                if r2["from"] == mid and r2["to"] == b:
                    return f1 * r2["factor"]
                if r2["to"] == mid and r2["from"] == b:
                    return f1 / r2["factor"]
    return None


def convert(value: float, from_unit: str | None, to_unit: str | None, parameter_id: str | None = None) -> float | None:
    f = conversion_factor(from_unit, to_unit, parameter_id)
    return None if f is None else value * f


def units_compatible(a: str | None, b: str | None, parameter_id: str | None = None) -> bool:
    return conversion_factor(a, b, parameter_id) is not None
