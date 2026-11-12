"""Panel benchmark: synthetic lab reports for the 10 priority panels, with values drawn from real-world distributions.

* Values are sampled independently per test from the aggregate percentiles in data/reference/population_stats.json
  (built from NHANES + UCI datasets by scripts/datasets/build_reference_data.py). Each report is therefore synthetic:
  no row corresponds to a real person (CLAUDE.md: no real patient data in tests).
* Printed reference ranges are typical Indian-lab style ranges chosen for the benchmark only; FITSCAN always reads the
  range printed on the report (BR-01), so these are test inputs, not clinical guidance.
* Every report also contains distractor lines (method sub-lines, notes, interpretation paragraphs, page footers)
  that must NOT become test rows.
"""
from __future__ import annotations

import json
import random
from bisect import bisect_left
from functools import lru_cache
from pathlib import Path

from tests.fixtures.synthetic_reports import Expected, Layout

STATS = Path(__file__).resolve().parents[2] / "data" / "reference" / "population_stats.json"

# parameter_id: (names as labs print them, [(unit as printed, factor from default unit, decimals)], printed range in
# default unit as (low, high) - either may be None for "< x" / "> x" styles)
SPEC: dict[str, tuple[list[str], list[tuple[str, float, int]], tuple[float | None, float | None]]] = {
    # CBC
    "hemoglobin": (["Haemoglobin", "Hemoglobin (Hb)"], [("g/dL", 1, 1)], (13.0, 17.0)),
    "rbc_count": (["Total RBC Count", "RBC Count"], [("million/cumm", 1, 2), ("10^12/L", 1, 2)], (4.5, 5.5)),
    "wbc_count": (["Total Leucocyte Count (TLC)", "WBC Count"], [("cells/cumm", 1000, 0), ("10^9/L", 1, 2)], (4.0, 10.0)),
    "platelet_count": (["Platelet Count"], [("lakhs/cumm", 0.01, 2), ("10^3/uL", 1, 0)], (150, 410)),
    "hematocrit": (["Packed Cell Volume (PCV)", "Hematocrit"], [("%", 1, 1)], (40.0, 50.0)),
    "mcv": (["MCV", "Mean Corpuscular Volume (MCV)"], [("fL", 1, 1)], (83.0, 101.0)),
    "mch": (["MCH"], [("pg", 1, 1)], (27.0, 32.0)),
    "mchc": (["MCHC"], [("g/dL", 1, 1)], (31.5, 34.5)),
    "rdw_cv": (["RDW-CV", "Red Cell Distribution Width (RDW-CV)"], [("%", 1, 1)], (11.6, 14.0)),
    "neutrophils_pct": (["Neutrophils"], [("%", 1, 1)], (40.0, 80.0)),
    "lymphocytes_pct": (["Lymphocytes"], [("%", 1, 1)], (20.0, 40.0)),
    "eosinophils_pct": (["Eosinophils"], [("%", 1, 1)], (1.0, 6.0)),
    "neutrophils_abs": (["Absolute Neutrophil Count"], [("10^9/L", 1, 2)], (2.0, 7.0)),
    # Lipid
    "cholesterol_total": (["Total Cholesterol", "Cholesterol - Total"], [("mg/dL", 1, 0)], (None, 200)),
    "hdl": (["HDL Cholesterol", "HDL - Direct"], [("mg/dL", 1, 0)], (40, None)),
    "ldl": (["LDL Cholesterol", "LDL Cholesterol - Calculated"], [("mg/dL", 1, 0)], (None, 100)),
    "triglycerides": (["Triglycerides", "Serum Triglycerides"], [("mg/dL", 1, 0)], (None, 150)),
    # Diabetes
    "glucose_fasting": (["Glucose - Fasting", "Fasting Blood Sugar (FBS)"], [("mg/dL", 1, 0)], (70, 100)),
    "hba1c": (["HbA1c", "Glycosylated Haemoglobin (HbA1c)"], [("%", 1, 1)], (4.0, 5.6)),
    "glucose_random": (["Random Blood Sugar (RBS)"], [("mg/dL", 1, 0)], (70, 140)),
    # Kidney
    "creatinine": (["Serum Creatinine", "Creatinine"], [("mg/dL", 1, 2)], (0.7, 1.3)),
    "urea": (["Blood Urea", "Urea"], [("mg/dL", 1, 0)], (17, 43)),
    "bun": (["Blood Urea Nitrogen (BUN)"], [("mg/dL", 1, 1)], (7.0, 20.0)),
    "egfr": (["eGFR"], [("mL/min/1.73m2", 1, 0)], (90, None)),
    "uric_acid": (["Uric Acid", "Serum Uric Acid"], [("mg/dL", 1, 1)], (3.5, 7.2)),
    # Liver
    "alt_sgpt": (["SGPT (ALT)", "Alanine Aminotransferase (ALT)"], [("U/L", 1, 0)], (0, 41)),
    "ast_sgot": (["SGOT (AST)", "Aspartate Aminotransferase (AST)"], [("U/L", 1, 0)], (0, 40)),
    "bilirubin_total": (["Bilirubin - Total", "Total Bilirubin"], [("mg/dL", 1, 2)], (0.3, 1.2)),
    "bilirubin_direct": (["Bilirubin - Direct", "Direct Bilirubin"], [("mg/dL", 1, 2)], (0.0, 0.3)),
    "albumin": (["Albumin", "Serum Albumin"], [("g/dL", 1, 1)], (3.5, 5.2)),
    "alp": (["Alkaline Phosphatase", "ALP"], [("U/L", 1, 0)], (40, 129)),
    "total_protein": (["Total Protein"], [("g/dL", 1, 1)], (6.4, 8.3)),
    "ggt": (["GGT", "Gamma GT (GGTP)"], [("U/L", 1, 0)], (None, 60)),
    # Thyroid
    "tsh": (["TSH", "Thyroid Stimulating Hormone (TSH)"], [("uIU/mL", 1, 2)], (0.27, 4.2)),
    "t3_total": (["Total T3", "T3 - Total"], [("ng/dL", 1, 0)], (80, 200)),
    "t4_total": (["Total T4", "T4 - Total"], [("ug/dL", 1, 1)], (5.1, 14.1)),
    "ft4": (["Free T4", "FT4"], [("ng/dL", 1, 2)], (0.93, 1.7)),
    # Vitamins
    "vitamin_b12": (["Vitamin B12", "Cyanocobalamin (Vitamin B12)"], [("pg/mL", 1, 0)], (211, 911)),
    "vitamin_d": (["Vitamin D (25-OH)", "25 Hydroxy Vitamin D"], [("ng/mL", 1, 1)], (30.0, 100.0)),
    # Iron
    "ferritin": (["Ferritin", "Serum Ferritin"], [("ng/mL", 1, 1)], (30.0, 400.0)),
    "iron": (["Iron", "Serum Iron"], [("ug/dL", 1, 0)], (65, 175)),
    "tibc": (["Total Iron Binding Capacity (TIBC)", "TIBC"], [("ug/dL", 1, 0)], (250, 450)),
    "transferrin_sat": (["Transferrin Saturation", "% Transferrin Saturation"], [("%", 1, 1)], (20.0, 50.0)),
    # Electrolytes
    "sodium": (["Sodium", "Serum Sodium (Na+)"], [("mmol/L", 1, 0)], (136, 145)),
    "potassium": (["Potassium", "Serum Potassium (K+)"], [("mmol/L", 1, 1)], (3.5, 5.1)),
    "chloride": (["Chloride", "Serum Chloride (Cl-)"], [("mmol/L", 1, 0)], (98, 107)),
    "calcium": (["Calcium", "Serum Calcium"], [("mg/dL", 1, 1)], (8.6, 10.0)),
    # Inflammation
    "crp": (["C-Reactive Protein (CRP)", "CRP - Quantitative"], [("mg/L", 1, 1)], (None, 5.0)),
    "esr": (["ESR", "Erythrocyte Sedimentation Rate (ESR)"], [("mm/1st hr", 1, 0)], (0, 20)),
}

PANELS: dict[str, tuple[str, list[str]]] = {
    "cbc": ("CBC", ["hemoglobin", "rbc_count", "wbc_count", "platelet_count", "hematocrit", "mcv", "mch", "mchc",
                    "rdw_cv", "neutrophils_pct", "lymphocytes_pct", "eosinophils_pct", "neutrophils_abs"]),
    "lipid": ("LIPID", ["cholesterol_total", "hdl", "ldl", "triglycerides"]),
    "diabetes": ("SUGAR", ["glucose_fasting", "hba1c", "glucose_random"]),
    "kft": ("KFT", ["creatinine", "urea", "bun", "egfr", "uric_acid"]),
    "lft": ("LFT", ["alt_sgpt", "ast_sgot", "bilirubin_total", "bilirubin_direct", "albumin", "alp", "total_protein", "ggt"]),
    "thyroid": ("THYROID", ["tsh", "t3_total", "t4_total", "ft4"]),
    "vitamins": ("B12", ["vitamin_b12", "vitamin_d"]),
    "iron": ("IRON", ["ferritin", "iron", "tibc", "transferrin_sat"]),
    "electrolytes": ("KFT", ["sodium", "potassium", "chloride", "calcium"]),
    "inflammation": ("INFLAMMATION", ["crp", "esr"]),
}

TEMPLATES = [
    [("Test Name", 50), ("Result", 260), ("Unit", 340), ("Bio. Ref. Interval", 420)],
    [("Investigation", 50), ("Observed Value", 250), ("Flag", 335), ("Reference Range", 380), ("Units", 500)],
    [("Test Description", 50), ("Value", 270), ("Units", 345), ("Normal Range", 440)],
]
LABS = ["Demo Path Labs", "Sample Diagnostics Centre", "Test Health Laboratory", "Example Clinical Lab"]
METHOD_LINES = ["Calculated", "Flowcytometry", "Photometry", "Electrical Impedance", "CLIA", "Spectrophotometry"]
DISTRACTORS = [
    "Note: Results relate only to the sample tested. Please correlate clinically.",
    "Interpretation: values between 5.7 and 6.4 % may need follow up as advised by your doctor 2024",
    "Comments - Kindly correlate with clinical findings and other investigations.",
    "Booking Centre :4821 - Demo Health Pvt Ltd, Plot 12, Sector 3",
    "Page 1 of 2",
    "The authenticity of this report can be verified by scanning the QR code",
    "* Test performed on fully automated analyser",
]


@lru_cache
def _quantiles() -> dict[str, list[tuple[float, float]]]:
    """parameter_id -> [(percentile 0..1, value)] from the pooled real-world statistics."""
    data = json.loads(STATS.read_text(encoding="utf-8"))["parameters"]
    out = {}
    for pid, s in data.items():
        pts = [(float(k[1:].replace("_", ".")) / 100, v) for k, v in s["pooled"].items() if k.startswith("p")]
        out[pid] = sorted(pts)
    return out


def sample(pid: str, rng: random.Random) -> float:
    q = _quantiles().get(pid)
    if not q:  # no public dataset (e.g. ESR): plausible synthetic spread
        return rng.uniform(2, 60)
    u = rng.uniform(0.01, 0.99)
    ps = [p for p, _ in q]
    i = max(1, min(bisect_left(ps, u), len(q) - 1))
    (p0, v0), (p1, v1) = q[i - 1], q[i]
    return v0 + (v1 - v0) * ((u - p0) / (p1 - p0) if p1 > p0 else 0)


def _fmt(x: float, d: int) -> str:
    return f"{x:.{d}f}"


def _range_text(lo, hi, factor, d) -> str:
    def f(v):
        return _fmt(v * factor, d if factor == 1 else max(d, 0))
    if lo is not None and hi is not None:
        return f"{f(lo)} - {f(hi)}"
    return f"< {f(hi)}" if hi is not None else f"> {f(lo)}"


def build_reports(variants: int = 3, seed: int = 20261111) -> list[Layout]:
    rng = random.Random(seed)
    reports: list[Layout] = []
    for panel, (category, pids) in PANELS.items():
        for v in range(variants):
            cols = TEMPLATES[v % len(TEMPLATES)]
            has_flag = any(t == "Flag" for t, _ in cols)
            rows, expected = [], []
            for j, pid in enumerate(pids):
                names, units, (lo, hi) = SPEC[pid]
                name = names[(v + j) % len(names)]
                unit, factor, d = units[(v + j) % len(units)]
                value = round(sample(pid, rng) * factor, d)
                if d == 0:
                    value = float(int(value))
                plo = None if lo is None else round(lo * factor, d)
                phi = None if hi is None else round(hi * factor, d)
                status = "BELOW" if plo is not None and value < plo else "ABOVE" if phi is not None and value > phi else "WITHIN"
                flag = {"BELOW": "L", "ABOVE": "H"}.get(status, "")
                vtxt, rtxt = _fmt(value, d), _range_text(lo, hi, factor, d)
                cells = {"name": name, "value": vtxt, "unit": unit, "range": rtxt, "flag": flag if has_flag else ""}
                order = {"Test Name": "name", "Investigation": "name", "Test Description": "name", "Result": "value",
                         "Observed Value": "value", "Value": "value", "Unit": "unit", "Units": "unit", "Flag": "flag",
                         "Bio. Ref. Interval": "range", "Reference Range": "range", "Normal Range": "range"}
                rows.append([cells[order[t]] for t, _ in cols])
                expected.append(Expected(pid, value, plo, phi, status, unit, flag or None))
                if rng.random() < 0.25:  # method sub-line under the test name
                    rows.append([rng.choice(METHOD_LINES)] + [""] * (len(cols) - 1))
            for line in rng.sample(DISTRACTORS, 3):
                rows.insert(rng.randint(len(rows) // 2, len(rows)), [line] + [""] * (len(cols) - 1))
            lab = LABS[(v + len(reports)) % len(LABS)]
            day = 1 + (len(reports) % 27)
            reports.append(Layout(
                key=f"bench_{panel}_{v + 1}",
                header_lines=[lab.upper(), "Synthetic benchmark report - not a real patient",
                              f"Patient Name : Benchmark Person {len(reports) + 1:02d}      Age/Sex : 40 Y / M",
                              f"Collected On : {day:02d}/03/2025    Reported On : {day:02d}/03/2025"],
                columns=cols, rows=rows, expected=expected,
                meta={"lab_name": lab.upper(), "report_category": category, "panel": panel},
            ))
    return reports
