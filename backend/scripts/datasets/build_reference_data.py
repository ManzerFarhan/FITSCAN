"""Build FITSCAN's reference data from public, de-identified lab datasets.

    python scripts/datasets/build_reference_data.py            # download (cached) + build stats + report
    python scripts/datasets/build_reference_data.py --apply    # ...and widen dictionary sanity bounds

What the data is used for (and NOT used for):
  * Population statistics per test -> data-driven SANITY bounds (catching OCR slips such as a lost decimal point)
    and realistic value ranges for the synthetic benchmark reports.
  * It is NEVER used to diagnose, predict disease, or replace the lab's printed reference range (BR-01, BR-04).
    Disease labels in these datasets (CKD, liver disease, hepatitis) are deliberately ignored.
  * Only aggregate statistics are stored in the repo (data/reference/population_stats.json). Raw files are cached in
    data/external/ (git-ignored) and no individual rows are copied into fixtures or tests.

Sources (see docs/datasets.md for licences and citations):
  NHANES 2017-2018 (CDC/NCHS, public domain) - CBC, biochemistry, lipids, glucose, HbA1c, iron, ferritin, hs-CRP, vitamin D
  NHANES 2011-2012 THYROD_G - thyroid; NHANES 2005-2006 B12_D - vitamin B12/folate (most recent cycles with these tests)
  UCI Chronic Kidney Disease (Apollo Hospitals, Tamil Nadu, India; CC BY 4.0) - kidney/electrolytes/CBC, Indian patients
  UCI ILPD Indian Liver Patient Dataset (Andhra Pradesh, India; CC BY 4.0) - liver function, Indian patients
  UCI HCV data (Hannover, Germany; CC BY 4.0) - liver/kidney chemistry in SI units
"""
from __future__ import annotations

import argparse
import io
import json
import math
import sys
from datetime import date
from pathlib import Path

import httpx
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
EXT = ROOT / "data" / "external"
OUT = ROOT / "data" / "reference" / "population_stats.json"
PARAMS = ROOT / "data" / "dictionaries" / "parameters.json"
UA = {"User-Agent": "Mozilla/5.0 (FITSCAN reference-data build; educational project)"}
NH = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.xpt"

# (parameter_id, column, factor-to-FITSCAN-default-unit, source unit) per NHANES file
NHANES: dict[tuple[str, str], list[tuple[str, str, float, str]]] = {
    ("2017", "CBC_J"): [
        ("wbc_count", "LBXWBCSI", 1, "1000 cells/uL"), ("lymphocytes_pct", "LBXLYPCT", 1, "%"),
        ("monocytes_pct", "LBXMOPCT", 1, "%"), ("neutrophils_pct", "LBXNEPCT", 1, "%"),
        ("eosinophils_pct", "LBXEOPCT", 1, "%"), ("basophils_pct", "LBXBAPCT", 1, "%"),
        ("lymphocytes_abs", "LBDLYMNO", 1, "1000 cells/uL"), ("monocytes_abs", "LBDMONO", 1, "1000 cells/uL"),
        ("neutrophils_abs", "LBDNENO", 1, "1000 cells/uL"), ("eosinophils_abs", "LBDEONO", 1, "1000 cells/uL"),
        ("basophils_abs", "LBDBANO", 1, "1000 cells/uL"), ("rbc_count", "LBXRBCSI", 1, "million cells/uL"),
        ("hemoglobin", "LBXHGB", 1, "g/dL"), ("hematocrit", "LBXHCT", 1, "%"), ("mcv", "LBXMCVSI", 1, "fL"),
        ("mch", "LBXMCHSI", 1, "pg"), ("mchc", "LBXMC", 1, "g/dL"), ("rdw_cv", "LBXRDW", 1, "%"),
        ("platelet_count", "LBXPLTSI", 1, "1000 cells/uL"), ("mpv", "LBXMPSI", 1, "fL"),
        ("nrbc", "LBXNRBC", 1, "per 100 WBC"),
    ],
    ("2017", "BIOPRO_J"): [
        ("alt_sgpt", "LBXSATSI", 1, "U/L"), ("albumin", "LBXSAL", 1, "g/dL"), ("alp", "LBXSAPSI", 1, "U/L"),
        ("ast_sgot", "LBXSASSI", 1, "U/L"), ("bicarbonate", "LBXSC3SI", 1, "mmol/L"), ("bun", "LBXSBU", 1, "mg/dL"),
        ("urea", "LBXSBU", 2.1428, "mg/dL BUN x 2.14"), ("chloride", "LBXSCLSI", 1, "mmol/L"),
        ("ck_total", "LBXSCK", 1, "U/L"), ("creatinine", "LBXSCR", 1, "mg/dL"), ("globulin", "LBXSGB", 1, "g/dL"),
        ("glucose_random", "LBXSGL", 1, "mg/dL (non-fasting serum)"), ("ggt", "LBXSGTSI", 1, "U/L"),
        ("iron", "LBXSIR", 1, "ug/dL"), ("potassium", "LBXSKSI", 1, "mmol/L"), ("ldh", "LBXSLDSI", 1, "U/L"),
        ("sodium", "LBXSNASI", 1, "mmol/L"), ("phosphorus", "LBXSPH", 1, "mg/dL"),
        ("bilirubin_total", "LBXSTB", 1, "mg/dL"), ("total_protein", "LBXSTP", 1, "g/dL"),
        ("uric_acid", "LBXSUA", 1, "mg/dL"), ("calcium", "LBXSCA", 1, "mg/dL"),
    ],
    ("2017", "GHB_J"): [("hba1c", "LBXGH", 1, "%")],
    ("2017", "GLU_J"): [("glucose_fasting", "LBXGLU", 1, "mg/dL")],
    ("2017", "TCHOL_J"): [("cholesterol_total", "LBXTC", 1, "mg/dL")],
    ("2017", "HDL_J"): [("hdl", "LBDHDD", 1, "mg/dL")],
    ("2017", "TRIGLY_J"): [("triglycerides", "LBXTR", 1, "mg/dL"), ("ldl", "LBDLDL", 1, "mg/dL (Friedewald)")],
    ("2017", "FERTIN_J"): [("ferritin", "LBXFER", 1, "ng/mL")],
    ("2017", "FETIB_J"): [("tibc", "LBDTIB", 1, "ug/dL"), ("uibc", "LBXUIB", 1, "ug/dL"),
                          ("transferrin_sat", "LBDPCT", 1, "%")],
    ("2017", "HSCRP_J"): [("crp", "LBXHSCRP", 1, "mg/L"), ("hs_crp", "LBXHSCRP", 1, "mg/L")],
    ("2017", "VID_J"): [("vitamin_d", "LBXVIDMS", 1 / 2.496, "nmol/L -> ng/mL")],
    ("2011", "THYROD_G"): [
        ("tsh", "LBXTSH1", 1, "uIU/mL"), ("ft4", "LBXT4F", 1, "ng/dL"), ("ft3", "LBXT3F", 1, "pg/mL"),
        ("t4_total", "LBXTT4", 1, "ug/dL"), ("t3_total", "LBXTT3", 1, "ng/dL"),
        ("anti_tpo", "LBXTPO", 1, "IU/mL"), ("anti_tg", "LBXATG", 1, "IU/mL"),
    ],
    ("2005", "B12_D"): [("vitamin_b12", "LBXB12", 1, "pg/mL")],
    ("2005", "FOLATE_D"): [("folate", "LBXFOL", 1, "ng/mL (serum folate)")],
}
NHANES_DEMO = ("2017", "DEMO_J")

UCI = {  # UCI's CSV export of each dataset
    "uci_ckd": "https://archive.ics.uci.edu/static/public/336/data.csv",
    "uci_ilpd": "https://archive.ics.uci.edu/static/public/225/data.csv",
    "uci_hcv": "https://archive.ics.uci.edu/static/public/571/data.csv",
}
# column -> (parameter_id, factor to FITSCAN default unit)
CKD_COLS = {"bgr": ("glucose_random", 1), "bu": ("urea", 1), "sc": ("creatinine", 1), "sod": ("sodium", 1),
            "pot": ("potassium", 1), "hemo": ("hemoglobin", 1), "pcv": ("hematocrit", 1),
            "wbcc": ("wbc_count", 0.001), "rbcc": ("rbc_count", 1)}
ILPD_COLS = {"TB": "bilirubin_total", "DB": "bilirubin_direct", "Alkphos": "alp", "Sgpt": "alt_sgpt", "Sgot": "ast_sgot",
             "TP": "total_protein", "ALB": "albumin", "A/G Ratio": "ag_ratio"}
HCV_COLS = {"ALB": ("albumin", 0.1), "ALP": ("alp", 1), "ALT": ("alt_sgpt", 1), "AST": ("ast_sgot", 1),
            "BIL": ("bilirubin_total", 1 / 17.1), "CHOL": ("cholesterol_total", 38.67), "CREA": ("creatinine", 1 / 88.4),
            "CGT": ("ggt", 1), "PROT": ("total_protein", 0.1)}

QUANTILES = [0, 0.1, 0.5, 1, 2.5, 5, 25, 50, 75, 95, 97.5, 99, 99.5, 99.9, 100]


def fetch(url: str, dest: Path) -> bytes:
    if dest.exists() and dest.stat().st_size > 100:
        return dest.read_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    r = httpx.get(url, headers=UA, follow_redirects=True, timeout=180)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return r.content


def read_xpt(year: str, name: str):
    import pandas as pd

    path = EXT / "nhanes" / f"{name}.xpt"
    fetch(NH.format(year=year, name=name), path)
    df = pd.read_sas(path, format="xport")
    return df


def clean(values) -> np.ndarray:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    a[np.abs(a) < 1e-10] = 0.0  # SAS stores exact zero as 5.4e-79
    return a


def summarize(a: np.ndarray) -> dict:
    q = np.percentile(a, QUANTILES)
    return {"n": int(a.size), **{f"p{str(k).replace('.', '_')}": round(float(v), 4) for k, v in zip(QUANTILES, q)},
            "mean": round(float(a.mean()), 4)}


def ckd_epi_2021(scr: np.ndarray, age: np.ndarray, female: np.ndarray) -> np.ndarray:
    k = np.where(female, 0.7, 0.9)
    alpha = np.where(female, -0.241, -0.302)
    ratio = scr / k
    return 142 * np.minimum(ratio, 1) ** alpha * np.maximum(ratio, 1) ** -1.200 * 0.9938 ** age * np.where(female, 1.012, 1)


def load_all() -> dict[str, list[dict]]:
    """parameter_id -> list of {source, column, unit, values(np.ndarray)}."""
    import pandas as pd

    out: dict[str, list[dict]] = {}

    def add(pid, source, column, unit, values):
        a = clean(values)
        if a.size >= 30:
            out.setdefault(pid, []).append({"source": source, "column": column, "unit": unit, "values": a})

    missing = []
    for (year, name), cols in NHANES.items():
        try:
            df = read_xpt(year, name)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {name}: {type(exc).__name__}: {exc}")
            continue
        for pid, col, factor, unit in cols:
            if col not in df.columns:
                missing.append(f"{name}.{col}")
                continue
            add(pid, f"NHANES {name}", col, unit, df[col].to_numpy(dtype=float) * factor)
        print(f"  NHANES {name}: {len(df)} rows")

    # eGFR (CKD-EPI 2021, adults) from NHANES creatinine + age/sex
    try:
        demo = read_xpt(*NHANES_DEMO)[["SEQN", "RIDAGEYR", "RIAGENDR"]]
        bio = read_xpt("2017", "BIOPRO_J")[["SEQN", "LBXSCR"]]
        m = bio.merge(demo, on="SEQN").dropna()
        m = m[(m.RIDAGEYR >= 18) & (m.LBXSCR > 0)]
        egfr = ckd_epi_2021(m.LBXSCR.to_numpy(), m.RIDAGEYR.to_numpy(), (m.RIAGENDR == 2).to_numpy())
        add("egfr", "NHANES BIOPRO_J+DEMO_J (CKD-EPI 2021, adults)", "LBXSCR,RIDAGEYR,RIAGENDR", "mL/min/1.73m2", egfr)
    except Exception as exc:  # noqa: BLE001
        print(f"  ! eGFR: {exc}")

    # UCI CKD (Apollo Hospitals, India)
    df = pd.read_csv(io.BytesIO(fetch(UCI["uci_ckd"], EXT / "uci" / "ckd.csv")))
    for col, (pid, factor) in CKD_COLS.items():
        add(pid, "UCI Chronic Kidney Disease (India)", col, "", pd.to_numeric(df[col], errors="coerce") * factor)
    print(f"  UCI CKD: {len(df)} rows")

    # UCI ILPD (Andhra Pradesh, India)
    df = pd.read_csv(io.BytesIO(fetch(UCI["uci_ilpd"], EXT / "uci" / "ilpd.csv")))
    for col, pid in ILPD_COLS.items():
        add(pid, "UCI ILPD Indian Liver Patient Dataset", col, "", pd.to_numeric(df[col], errors="coerce"))
    print(f"  UCI ILPD: {len(df)} rows")

    # UCI HCV (Hannover, SI units)
    df = pd.read_csv(io.BytesIO(fetch(UCI["uci_hcv"], EXT / "uci" / "hcv.csv")))
    for col, (pid, factor) in HCV_COLS.items():
        if col in df.columns:
            add(pid, "UCI HCV data (Germany)", col, "SI converted", pd.to_numeric(df[col], errors="coerce") * factor)
    print(f"  UCI HCV: {len(df)} rows")

    if missing:
        print("  ! columns not found:", ", ".join(missing))
    return out


def build(apply: bool) -> None:
    data = load_all()
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    by_id = {p["parameter_id"]: p for p in params["parameters"]}
    stats = {"generated": date.today().isoformat(),
             "note": "Aggregate statistics only, in FITSCAN default units. Used for sanity bounds and synthetic "
                     "benchmarks - never as reference ranges and never for diagnosis.",
             "parameters": {}}
    changes = []
    for pid, sources in sorted(data.items()):
        if pid not in by_id:
            continue
        pooled = np.concatenate([s["values"] for s in sources])
        b = by_id[pid]
        outside = float(((pooled < b["plausible_min"]) | (pooled > b["plausible_max"])).mean())
        stats["parameters"][pid] = {
            "unit": b["default_unit"],
            "category": b["category"],
            "share_outside_sanity_bounds": round(outside, 5),
            "pooled": summarize(pooled),
            "sources": [{"source": s["source"], "column": s["column"], "unit_note": s["unit"], **summarize(s["values"])}
                        for s in sources],
        }
        # Widen-only sanity bounds so real (even extreme) values are never called implausible. Uses the 0.1th/99.9th
        # percentiles, not min/max, so single data-entry errors in a source (e.g. sodium 4.5) can't distort them.
        p = by_id[pid]
        lo, hi = (float(x) for x in np.percentile(pooled, [0.1, 99.9]))
        new_lo = min(p["plausible_min"], _sig2_down(lo * 0.9))
        new_hi = max(p["plausible_max"], _sig2_up(hi * 1.1))
        if p["default_unit"] == "%" and pid not in PCT_CAN_EXCEED_100:
            new_hi = min(new_hi, 100)
        if (new_lo, new_hi) != (p["plausible_min"], p["plausible_max"]):
            changes.append(f"{pid}: [{p['plausible_min']}, {p['plausible_max']}] -> [{new_lo}, {new_hi}] (data {lo:.3g}..{hi:.3g})")
            if apply:
                p["plausible_min"], p["plausible_max"] = new_lo, new_hi
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(stats, indent=1), encoding="utf-8")
    total = sum(v["pooled"]["n"] for v in stats["parameters"].values())
    print(f"\nWrote {OUT.relative_to(ROOT)}: {len(stats['parameters'])} parameters, {total:,} values")
    worst = sorted(((v["share_outside_sanity_bounds"], k) for k, v in stats["parameters"].items()), reverse=True)[:5]
    print("Highest share of real values flagged by sanity bounds: "
          + ", ".join(f"{k} {s:.2%}" for s, k in worst))
    print(("Applied" if apply else "Would apply") + f" {len(changes)} bound change(s):")
    for c in changes:
        print("  " + c)
    if apply and changes:
        PARAMS.write_text(json.dumps(params, indent=2, ensure_ascii=False), encoding="utf-8")
    write_doc(stats, by_id)


SOURCE_INFO = [
    ("NHANES 2017-2018 (cycle J)",
     ("U.S. CDC / National Center for Health Statistics - National Health and Nutrition Examination Survey, "
      "laboratory files CBC_J, BIOPRO_J, GHB_J, GLU_J, TCHOL_J, HDL_J, TRIGLY_J, FERTIN_J, FETIB_J, HSCRP_J, VID_J, DEMO_J"),
     "Public domain (U.S. government work)", "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2017"),
    ("NHANES 2011-2012 (cycle G)", "Thyroid profile file THYROD_G (most recent NHANES cycle with thyroid tests)",
     "Public domain", "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2011"),
    ("NHANES 2005-2006 (cycle D)", "Vitamin B12 (B12_D) and folate (FOLATE_D) - most recent cycle with serum B12",
     "Public domain", "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?BeginYear=2005"),
    ("UCI Chronic Kidney Disease",
     "L. Rubini, P. Soundarapandian, P. Eswaran (2015). 400 patients, Apollo Hospitals, Tamil Nadu, India",
     "CC BY 4.0", "https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease"),
    ("UCI ILPD (Indian Liver Patient Dataset)",
     "B. Ramana, N. Venkateswarlu (2012). 583 patients, north-east Andhra Pradesh, India",
     "CC BY 4.0", "https://archive.ics.uci.edu/dataset/225/ilpd+indian+liver+patient+dataset"),
    ("UCI HCV data",
     "R. Lichtinghagen, F. Klawonn, G. Hoffmann (2020). 615 blood donors and hepatitis C patients, Hannover, Germany",
     "CC BY 4.0", "https://archive.ics.uci.edu/dataset/571/hcv+data"),
]


def write_doc(stats: dict, by_id: dict) -> None:
    rows = []
    for pid, s in sorted(stats["parameters"].items(), key=lambda kv: (kv[1]["category"], kv[0])):
        src = "; ".join(f"{x['source']} `{x['column']}` (n={x['n']:,})" for x in s["sources"])
        p = s["pooled"]
        rows.append(f"| {s['category']} | {by_id[pid]['canonical_name']} | {p['n']:,} | {src} | "
                    f"{p['p1']:.3g} - {p['p50']:.3g} - {p['p99']:.3g} {s['unit']} | {s['share_outside_sanity_bounds']:.2%} |")
    total = sum(s["pooled"]["n"] for s in stats["parameters"].values())
    doc = f"""# FITSCAN - Reference datasets

_Generated {stats['generated']} by `backend/scripts/datasets/build_reference_data.py`. Do not edit by hand._

## What these datasets are used for

| Use | Detail |
|---|---|
| Sanity bounds | Each test's `plausible_min/max` (used only to catch OCR slips such as a lost decimal point) must accept at least 99.8 % of real values. The last column below shows how many real values a bound would flag. |
| Benchmark realism | `backend/tests/fixtures/panel_benchmark.py` draws test values from these distributions to build 30 synthetic reports for the 10 priority panels. |
| **Not used for** | Diagnosis, disease prediction, risk scores or reference ranges. FITSCAN always uses the range printed on the user's own report (BR-01) and never diagnoses (BR-04). The datasets' disease labels (CKD, liver disease, hepatitis) are ignored. |

Only aggregate statistics are stored (`backend/data/reference/population_stats.json`). Raw downloads are cached in
`backend/data/external/` (git-ignored); no individual record is copied into the app, tests or fixtures.

## Sources

| Dataset | Description | Licence | Link |
|---|---|---|---|
""" + "\n".join(f"| {a} | {b} | {c} | {d} |" for a, b, c, d in SOURCE_INFO) + f"""

## Records per test ({len(stats['parameters'])} tests, {total:,} values)

| Panel | Test | Records | Source (dataset `column`, records) | 1st - 50th - 99th percentile | Real values outside sanity bounds |
|---|---|---|---|---|---|
""" + "\n".join(rows) + """

Notes
- eGFR is calculated from NHANES creatinine, age and sex with the CKD-EPI 2021 equation (adults only).
- Urea is calculated from NHANES BUN (urea = BUN x 2.14); UCI CKD reports blood urea directly.
- NHANES vitamin D (nmol/L) is converted to ng/mL (/2.496); UCI HCV values in SI units are converted to FITSCAN units.
- CRP and hs-CRP share the NHANES high-sensitivity CRP measurement.
- ESR has no suitable public dataset; its bounds and benchmark values are set by hand.
"""
    path = ROOT.parent / "docs" / "datasets.md"
    path.write_text(doc, encoding="utf-8")
    print(f"Wrote {path.relative_to(ROOT.parent)}")


PCT_CAN_EXCEED_100: set[str] = set()


def _sig2_down(x: float) -> float:
    if x <= 0:
        return 0
    m = 10 ** (math.floor(math.log10(x)) - 1)
    return round(math.floor(x / m) * m, 6)


def _sig2_up(x: float) -> float:
    if x <= 0:
        return 0
    m = 10 ** (math.floor(math.log10(x)) - 1)
    return round(math.ceil(x / m) * m, 6)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write widened sanity bounds into parameters.json")
    build(ap.parse_args().apply)
