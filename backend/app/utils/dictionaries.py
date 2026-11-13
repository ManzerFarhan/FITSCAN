"""Cached loaders for data/dictionaries/*.json."""
import json
from functools import lru_cache
from pathlib import Path

DICT_DIR = Path(__file__).resolve().parents[2] / "data" / "dictionaries"


def _load(name: str) -> dict:
    return json.loads((DICT_DIR / name).read_text(encoding="utf-8"))


@lru_cache
def parameters() -> dict[str, dict]:
    """Core dictionary first, then the extended one (scripts/build_extended_dictionary.py); core entries win."""
    out: dict[str, dict] = {}
    for name in ("parameters.json", "parameters_extended.json"):
        if (DICT_DIR / name).exists():
            for p in _load(name)["parameters"]:
                out.setdefault(p["parameter_id"], p)
    return out


@lru_cache
def unit_conversions() -> dict:
    return _load("unit_conversions.json")
