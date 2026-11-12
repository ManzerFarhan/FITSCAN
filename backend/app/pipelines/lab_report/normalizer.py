"""Test-name normalization: raw name -> canonical parameter_id (FR-LAB-5)."""
from __future__ import annotations

import re
from functools import lru_cache

from pydantic import BaseModel
from rapidfuzz import fuzz, process

from app.utils import dictionaries

_FILLER = {"serum", "s", "blood", "level", "levels", "test", "plasma", "method", "calculated", "by"}
FUZZY_CUTOFF = 86


class NameMatch(BaseModel):
    parameter_id: str | None
    canonical_name: str | None = None
    category: str | None = None
    score: float  # 0..1
    method: str  # exact | filtered | fuzzy | none


def normalize_key(text: str) -> str:
    t = text.lower().replace("haem", "hem")
    t = re.sub(r"\[.*?\]", " ", t)
    t = re.sub(r"[^a-z0-9+]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _strip_parens(text: str) -> str:
    return re.sub(r"\(.*?\)", " ", text)


def _strip_filler(key: str) -> str:
    return " ".join(w for w in key.split() if w not in _FILLER)


@lru_cache
def _index() -> dict[str, str]:
    idx: dict[str, str] = {}
    for pid, p in dictionaries.parameters().items():
        for syn in [p["canonical_name"], *p["synonyms"]]:
            idx.setdefault(normalize_key(syn), pid)
            idx.setdefault(_strip_filler(normalize_key(syn)), pid)
    idx.pop("", None)
    return idx


def _compact(key: str) -> str:
    return key.replace(" ", "")


def _fix_l(key: str) -> str:
    """'lron' -> 'iron': a word starting with l followed by a consonant other than l/y is almost always an OCR'd I."""
    return re.sub(r"\bl(?=[bcdfghjkmnpqrstvwxz])", "i", key)


@lru_cache
def _compact_index() -> dict[str, str]:
    out: dict[str, str] = {}
    for key, pid in _index().items():
        out.setdefault(_compact(key), pid)
    return out


def _make(pid: str | None, score: float, method: str) -> NameMatch:
    if pid is None:
        return NameMatch(parameter_id=None, score=score, method=method)
    p = dictionaries.parameters()[pid]
    return NameMatch(parameter_id=pid, canonical_name=p["canonical_name"], category=p["category"], score=score, method=method)


def match_parameter(raw_name: str) -> NameMatch:
    idx = _index()
    variants = [normalize_key(raw_name), normalize_key(_strip_parens(raw_name))]
    # also try the parenthetical content itself, e.g. "Packed Cell Volume (PCV)" -> "pcv"
    variants += [normalize_key(m) for m in re.findall(r"\((.*?)\)", raw_name)]
    # a leading serial number ("1 Haemoglobin", "12. ESR") - tried after the full name ("25 Hydroxy Vitamin D")
    variants += [re.sub(r"^\d{1,3} ", "", v) for v in variants if re.match(r"^\d{1,3} ", v)]
    for v in variants:
        if v in idx:
            return _make(idx[v], 1.0, "exact")
    for v in variants:
        f = _strip_filler(v)
        if f in idx:
            return _make(idx[f], 0.97, "filtered")
    # OCR often drops spaces ("TotalCholesterol", "VitaminB12") or reads a capital I as l ("lron", "Serum lron").
    cidx = _compact_index()
    for v in variants:
        for c in {_compact(v), _compact(_fix_l(v)), _compact(_strip_filler(_fix_l(v)))}:
            if len(c) >= 4 and c in cidx:
                return _make(cidx[c], 0.95, "compact")
    query = _strip_filler(variants[1]) or variants[0]
    if len(query) >= 4:
        best = process.extractOne(query, list(idx.keys()), scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_CUTOFF)
        if best:
            key, score, _ = best
            # very short dictionary keys (e.g. "na", "k") are never fuzzy targets
            if len(key) >= 4:
                return _make(idx[key], round(score / 100, 3), "fuzzy")
    return _make(None, 0.0, "none")
