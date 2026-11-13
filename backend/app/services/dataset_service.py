"""What FITSCAN knows (FR-ADM-14): the test dictionary, population reference data and the knowledge library.

Read-only view for the admin panel, so the owner can see what is covered and ask for what is missing.
"""
from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache

from app.pipelines.lab_report.normalizer import match_parameter
from app.utils import dictionaries
from app.utils.dictionaries import DICT_DIR

REFERENCE_FILE = DICT_DIR.parent / "reference" / "population_stats.json"

CATEGORY_LABELS = {
    "CBC": "Complete Blood Count", "LFT": "Liver Function", "KFT": "Kidney Function & Electrolytes",
    "LIPID": "Lipid Profile", "THYROID": "Thyroid", "SUGAR": "Sugar / Diabetes", "B12": "Vitamin B12 & Folate",
    "VITAMIN_D": "Vitamin D", "IRON": "Iron Studies", "COAG": "Coagulation", "CARDIAC": "Heart Markers",
    "HORMONE": "Hormones", "INFLAMMATION": "Inflammation & Immunity", "URINE": "Urine & Stool", "BLOOD_GAS": "Blood Gas",
    "VITAMINS": "Vitamins & Minerals", "TUMOR_MARKER": "Tumour Markers", "INFECTION": "Infection Tests",
    "AUTOIMMUNE": "Autoimmune", "OTHER": "Other",
}

SOURCES = [
    {"name": "Core test dictionary", "kind": "dictionary", "file": "backend/data/dictionaries/parameters.json",
     "what": "Routine panels: CBC, liver, kidney, lipids, thyroid, sugar, iron, vitamins B12/D, hormones, heart, clotting.",
     "used_for": "Recognising printed test names (with spelling/OCR variants) and units."},
    {"name": "Extended test dictionary", "kind": "dictionary", "file": "backend/data/dictionaries/parameters_extended.json",
     "what": "Urine & stool, blood gas, tumour markers, infection serology, autoimmune, more vitamins/minerals, "
             "hormones, clotting factors and medicine levels. Built by backend/scripts/build_extended_dictionary.py.",
     "used_for": "Recognising printed test names beyond the routine panels."},
    {"name": "Population reference data (NHANES + UCI)", "kind": "reference", "file": "backend/data/reference/population_stats.json",
     "what": "Aggregate statistics (percentiles only, no individual records) from US CDC NHANES 2017-18 / 2011-12 / 2005-06 "
             "and the UCI Chronic Kidney Disease (India), Indian Liver Patient and HCV datasets.",
     "used_for": "Sanity checks that catch reading slips (e.g. a lost decimal point). Never used as normal ranges or for diagnosis."},
    {"name": "Health knowledge library", "kind": "knowledge", "file": "backend/data/kb/*.yaml",
     "what": "Plain-language summaries from MedlinePlus, NIH and NHS, each with its source link.",
     "used_for": "Cited explanations and the chatbot's answers."},
]


@lru_cache
def _reference() -> dict:
    try:
        return json.loads(REFERENCE_FILE.read_text(encoding="utf-8")).get("parameters", {})
    except FileNotFoundError:
        return {}


@lru_cache
def _core_ids() -> frozenset[str]:
    return frozenset(p["parameter_id"] for p in json.loads((DICT_DIR / "parameters.json").read_text(encoding="utf-8"))["parameters"])


def _kb_docs():
    from app.rag.ingest import load_documents

    return load_documents()


def dataset() -> dict:
    params = dictionaries.parameters()
    ref = _reference()
    docs = _kb_docs()
    kb_by_test = Counter(pid for d in docs for pid in d.parameters)
    core = _core_ids()
    tests = []
    for pid, p in params.items():
        r = ref.get(pid)
        pooled = (r or {}).get("pooled") or {}
        tests.append({
            "id": pid, "name": p["canonical_name"], "category": p["category"],
            "category_label": CATEGORY_LABELS.get(p["category"], p["category"]),
            "source": "core" if pid in core else "extended",
            "unit": p.get("default_unit"), "plausible_min": p.get("plausible_min"), "plausible_max": p.get("plausible_max"),
            "synonyms": p.get("synonyms", []), "about": p.get("about"), "kb_articles": kb_by_test.get(pid, 0),
            "reference": {
                "n": pooled.get("n"), "p2_5": pooled.get("p2_5"), "p50": pooled.get("p50"), "p97_5": pooled.get("p97_5"),
                "unit": r.get("unit"), "sources": sorted({s["source"] for s in r.get("sources", [])}),
            } if r else None,
        })
    tests.sort(key=lambda t: (t["category_label"], t["name"].lower()))
    cats = Counter(t["category"] for t in tests)
    ref_sources = Counter(s["source"] for r in ref.values() for s in r.get("sources", []))
    ref_values = Counter()
    for r in ref.values():
        for s in r.get("sources", []):
            ref_values[s["source"]] += s.get("n") or 0
    return {
        "summary": {
            "tests": len(tests), "names": sum(1 + len(t["synonyms"]) for t in tests), "categories": len(cats),
            "core": sum(t["source"] == "core" for t in tests), "extended": sum(t["source"] == "extended" for t in tests),
            "with_reference": sum(t["reference"] is not None for t in tests),
            "reference_values": sum(ref_values.values()), "kb_articles": len(docs),
            "with_kb": sum(t["kb_articles"] > 0 for t in tests),
            "units": len(dictionaries.unit_conversions()["aliases"]),
        },
        "sources": SOURCES,
        "categories": [{"category": c, "label": CATEGORY_LABELS.get(c, c), "tests": n}
                       for c, n in sorted(cats.items(), key=lambda kv: -kv[1])],
        "tests": tests,
        "reference_sources": [{"source": s, "tests": n, "values": ref_values[s]} for s, n in ref_sources.most_common()],
        "knowledge": [{"title": d.title, "source": d.source, "url": d.url,
                       "tests": [params[pid]["canonical_name"] for pid in d.parameters if pid in params]} for d in docs],
    }


def check_name(name: str) -> dict:
    """How FITSCAN would read a printed test name - to see quickly whether something is missing."""
    m = match_parameter(name)
    return {"input": name, "recognised": m.parameter_id is not None, "test_id": m.parameter_id,
            "test_name": m.canonical_name, "category": m.category, "confidence": round(m.score, 3), "method": m.method}
