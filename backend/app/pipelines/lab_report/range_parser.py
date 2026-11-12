"""Reference-range parsing (FR-LAB-10). Always parses the LAB'S OWN range text (BR-01).

Supported forms: "12-16", "12.0 – 16.0", "12 to 16", "< 200", "<=200", "less than 200",
"up to 5.0", "> 40", ">= 40", "more than 40", sex-specific ("M: 13-17 F: 12-15"),
and tiered ranges where one tier is labelled normal/desirable/optimal.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel

NUM = r"(\d+(?:\.\d+)?)"
RangeKind = Literal["between", "upper", "lower", "unparsed", "sex_specific"]


class RefRange(BaseModel):
    raw: str | None = None
    low: float | None = None
    high: float | None = None
    low_inclusive: bool = True
    high_inclusive: bool = True
    kind: RangeKind = "unparsed"

    @property
    def parsed(self) -> bool:
        return self.kind in ("between", "upper", "lower")


def _clean(text: str) -> str:
    t = text.strip()
    t = t.replace("–", "-").replace("—", "-").replace("−", "-").replace("≤", "<=").replace("≥", ">=")
    t = re.sub(r"(?<=\d),(?=\d{2,3}\b)", "", t)  # 1,50,000 -> 150000
    t = re.sub(r"\s+", " ", t)
    return t


_SEX_PATTERNS = {
    "M": r"(?:\bmales?\b|\bmen\b|\bm\b)\s*[:\-=]?\s*",
    "F": r"(?:\bfemales?\b|\bwomen\b|\bf\b)\s*[:\-=]?\s*",
}
_NORMAL_TIER = re.compile(r"\b(?:normal|desirable|optimal|non[- ]?diabetic|sufficient|adequate)\b\s*[:\-]?\s*", re.IGNORECASE)


def _parse_simple(t: str) -> RefRange | None:
    s = t.strip().strip("()[]").strip()
    m = re.fullmatch(rf"{NUM}\s*(?:-|to)\s*{NUM}(?:\s*[a-zA-Zµ%/^0-9.]*)?", s, re.IGNORECASE)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        if lo <= hi:
            return RefRange(low=lo, high=hi, kind="between")
        return None
    m = re.fullmatch(rf"(<=|<|less than or equal to|less than|up ?to|upto|below|max\.?|maximum)\s*:?\s*{NUM}.*", s, re.IGNORECASE)
    if m:
        op = m.group(1).lower()
        inclusive = op in ("<=", "less than or equal to", "up to", "upto", "max", "max.", "maximum")
        return RefRange(high=float(m.group(2)), high_inclusive=inclusive, kind="upper")
    m = re.fullmatch(rf"(>=|>|more than or equal to|more than|greater than|above|min\.?|minimum|at least)\s*:?\s*{NUM}.*", s, re.IGNORECASE)
    if m:
        op = m.group(1).lower()
        inclusive = op in (">=", "more than or equal to", "min", "min.", "minimum", "at least")
        return RefRange(low=float(m.group(2)), low_inclusive=inclusive, kind="lower")
    return None


def _sex_ranges(t: str) -> dict[str, RefRange]:
    found: dict[str, RefRange] = {}
    for sex, pat in _SEX_PATTERNS.items():
        m = re.search(pat + r"([^;,/|]*?)(?=(?:" + _SEX_PATTERNS["M" if sex == "F" else "F"] + r")|[;,|/]|$)", t, re.IGNORECASE)
        if m:
            r = _parse_simple(m.group(1))
            if r:
                found[sex] = r
    return found


def parse_range(raw: str | None, sex: str | None = None) -> RefRange:
    if raw is None or not str(raw).strip():
        return RefRange(raw=raw, kind="unparsed")
    t = _clean(str(raw))

    simple = _parse_simple(t)
    if simple:
        return simple.model_copy(update={"raw": raw})

    sexed = _sex_ranges(t)
    if len(sexed) == 2 or (sexed and sex):
        key = (sex or "").upper()[:1]
        if key in sexed:
            return sexed[key].model_copy(update={"raw": raw})
        return RefRange(raw=raw, kind="sex_specific")  # don't guess which applies

    tier = _NORMAL_TIER.search(t)
    if tier:
        rest = t[tier.end():]
        rest = re.split(r"[;|]|\b(?:borderline|high|low|very high|pre[- ]?diabetic|diabetic|deficient|insufficient)\b", rest, 1, flags=re.IGNORECASE)[0]
        r = _parse_simple(rest.strip(" ,"))
        if r:
            return r.model_copy(update={"raw": raw})

    return RefRange(raw=raw, kind="unparsed")
