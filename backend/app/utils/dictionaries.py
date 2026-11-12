"""Cached loaders for data/dictionaries/*.json."""
import json
from functools import lru_cache
from pathlib import Path

DICT_DIR = Path(__file__).resolve().parents[2] / "data" / "dictionaries"


def _load(name: str) -> dict:
    return json.loads((DICT_DIR / name).read_text(encoding="utf-8"))


@lru_cache
def parameters() -> dict[str, dict]:
    return {p["parameter_id"]: p for p in _load("parameters.json")["parameters"]}


@lru_cache
def unit_conversions() -> dict:
    return _load("unit_conversions.json")
