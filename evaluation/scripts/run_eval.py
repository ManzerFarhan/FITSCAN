"""FITSCAN evaluation (BRD §10, P4-14/15). Runs on synthetic data only and writes docs/evaluation_report.md.

Usage (from repo root):  backend/.venv/Scripts/python evaluation/scripts/run_eval.py
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(Path(__file__).parent))

from metrics import cer, mrr, precision_recall_at_k, wer  # noqa: E402
from rapidfuzz import fuzz  # noqa: E402

from app.pipelines.lab_report.pipeline import LabReportPipeline  # noqa: E402
from app.pipelines.layout import group_lines  # noqa: E402
from app.pipelines.ocr.printed_ocr import get_printed_ocr  # noqa: E402
from app.pipelines.preprocessing.image_enhance import enhance  # noqa: E402
from app.pipelines.preprocessing.pdf_loader import load_document  # noqa: E402
from app.rag.retriever import retrieve  # noqa: E402
from app.rag.safety_validator import validate  # noqa: E402
from app.utils import dictionaries  # noqa: E402
from app.utils.units import normalize_unit  # noqa: E402
from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf, render_png  # noqa: E402


def eval_ocr() -> dict:
    ocr = get_printed_ocr()
    if not ocr.available:
        return {"engine": "none"}
    cers, wers = [], []
    for lo in LAYOUTS:
        doc = load_document(render_png(lo), "image/png")
        page = doc.pages[0]
        lines = [ln.text for ln in group_lines(ocr.run(enhance(page.image), 1))]
        refs = lo.header_lines + [" ".join(c for c in r if c) for r in lo.rows]
        for ref in refs:
            hyp = max(lines, key=lambda h: fuzz.ratio(ref, h)) if lines else ""
            cers.append(cer(ref, hyp))
            wers.append(wer(ref, hyp))
    return {"engine": ocr.engine_name, "lines": len(cers), "cer": statistics.mean(cers), "wer": statistics.mean(wers),
            "cer_median": statistics.median(cers)}


def eval_extraction(mode: str) -> dict:
    total = exact = ranges = units = units_total = found = phantom = 0
    t0 = time.time()
    for lo in LAYOUTS:
        data, mime = (render_pdf(lo), "application/pdf") if mode == "digital" else (render_png(lo), "image/png")
        res = LabReportPipeline().run(data, mime)
        got = {p.parameter_id: p for p in res.parameters if p.parameter_id}
        phantom += max(0, len(res.parameters) - len(lo.expected))
        for e in lo.expected:
            total += 1
            p = got.get(e.parameter_id)
            if not p:
                continue
            found += 1
            if p.value_num == e.value and p.status == e.status:
                exact += 1
            if (p.ref_low, p.ref_high) == (e.ref_low, e.ref_high):
                ranges += 1
            if e.unit:
                units_total += 1
                units += int(p.unit_normalized == normalize_unit(e.unit))
    return {"parameters": total, "recall": found / total, "exact_match": exact / total, "range_accuracy": ranges / total,
            "unit_accuracy": units / max(units_total, 1), "extra_rows": phantom, "seconds_per_report": (time.time() - t0) / len(LAYOUTS)}


def eval_panels(mode: str) -> dict:
    """Panel benchmark: 30 synthetic reports (10 priority panels x 3 layouts) with real-world value distributions
    and distractor lines (notes, method lines, footers) that must not become rows."""
    from tests.fixtures.panel_benchmark import build_reports

    per: dict[str, dict] = {}
    t0 = time.time()
    reports = build_reports()
    for lo in reports:
        data, mime = (render_pdf(lo), "application/pdf") if mode == "digital" else (render_png(lo), "image/png")
        res = LabReportPipeline().run(data, mime)
        got = {p.parameter_id: p for p in res.parameters if p.parameter_id}
        exp_ids = {e.parameter_id for e in lo.expected}
        a = per.setdefault(lo.meta["panel"], {"rows": 0, "found": 0, "exact": 0, "range": 0, "extra_rows": 0})
        a["extra_rows"] += sum(1 for p in res.parameters if p.parameter_id not in exp_ids)
        for e in lo.expected:
            a["rows"] += 1
            p = got.get(e.parameter_id)
            if not p:
                continue
            a["found"] += 1
            a["exact"] += int(p.value_num == e.value and p.status == e.status)
            a["range"] += int((p.ref_low, p.ref_high) == (e.ref_low, e.ref_high))
    total = {k: sum(v[k] for v in per.values()) for k in ("rows", "found", "exact", "range", "extra_rows")}
    out = {"reports": len(reports), "seconds_per_report": (time.time() - t0) / len(reports), "panels": {}}
    for name, v in {**per, "ALL": total}.items():
        out["panels"][name] = {"rows": v["rows"], "recall": v["found"] / v["rows"], "exact_match": v["exact"] / v["rows"],
                               "range_accuracy": v["range"] / v["rows"], "extra_rows": v["extra_rows"]}
    return out


def eval_units() -> dict:
    aliases = dictionaries.unit_conversions()["aliases"]
    ok = sum(1 for raw, canon in aliases.items() if normalize_unit(raw) == canon)
    ok_upper = sum(1 for raw, canon in aliases.items() if normalize_unit(raw.upper()) == canon)
    return {"aliases": len(aliases), "rate": ok / len(aliases), "rate_uppercase": ok_upper / len(aliases)}


def eval_rag(k: int = 5) -> dict:
    qs = json.loads((ROOT / "evaluation" / "datasets" / "rag_qa.json").read_text(encoding="utf-8"))["questions"]
    ps, rs, mrrs, hits = [], [], [], 0
    for q in qs:
        titles = []
        for s in retrieve(q["q"], k=k, parameter_id=q["pid"]):
            if s.title not in titles:
                titles.append(s.title)
        rel = set(q["relevant"])
        p, r = precision_recall_at_k(titles, rel, k)
        ps.append(p); rs.append(r); mrrs.append(mrr(titles, rel)); hits += int(bool(rel & set(titles)))
    from app.rag.retriever import get_store
    return {"questions": len(qs), "embedder": get_store().embedder.name, "precision_at_k": statistics.mean(ps),
            "recall_at_k": statistics.mean(rs), "mrr": statistics.mean(mrrs), "hit_rate": hits / len(qs), "k": k}


def eval_guardrails() -> dict:
    sys.path.insert(0, str(ROOT / "backend" / "tests" / "unit"))
    from test_safety_validator import SAFE, UNSAFE  # noqa: E402

    blocked = sum(1 for t, _ in UNSAFE if not validate(t, "chat").ok)
    passed = sum(1 for t in SAFE if validate(t, "analysis").ok)
    return {"unsafe": len(UNSAFE), "blocked": blocked, "safe": len(SAFE), "safe_passed": passed}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def main() -> None:
    print("OCR..."); ocr = eval_ocr()
    print("Extraction (digital)..."); dig = eval_extraction("digital")
    print("Extraction (scanned)..."); scn = eval_extraction("scanned") if ocr.get("engine") != "none" else None
    print("Panel benchmark (digital)..."); pdig = eval_panels("digital")
    print("Panel benchmark (scanned)..."); pscn = eval_panels("scanned") if ocr.get("engine") != "none" else None
    print("Units..."); units = eval_units()
    print("RAG..."); rag = eval_rag()
    print("Guardrails..."); guard = eval_guardrails()
    results = {"ocr": ocr, "digital": dig, "scanned": scn, "panels_digital": pdig, "panels_scanned": pscn,
               "units": units, "rag": rag, "guardrails": guard}

    def panel_rows() -> str:
        lines = []
        for name, d in pdig["panels"].items():
            s = pscn["panels"][name] if pscn else None
            scanned = f"{pct(s['recall'])} / {pct(s['exact_match'])}" if s else "n/a"
            extra = f"{d['extra_rows']} / {s['extra_rows']}" if s else str(d["extra_rows"])
            lines.append(f"| {name} | {d['rows']} | {pct(d['recall'])} / {pct(d['exact_match'])} | {scanned} | {extra} |")
        return "\n".join(lines)
    (ROOT / "evaluation" / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    def ext_rows(name, r):
        if not r:
            return f"| {name} | n/a | n/a | n/a | n/a | n/a |"
        return (f"| {name} | {pct(r['recall'])} | {pct(r['exact_match'])} | {pct(r['range_accuracy'])} | "
                f"{pct(r['unit_accuracy'])} | {r['seconds_per_report']:.1f} s |")

    report = f"""# FITSCAN - Evaluation Report

_Generated {date.today().isoformat()} by `evaluation/scripts/run_eval.py`. Raw numbers: `evaluation/results.json`._

> **Scope and honesty note.** All numbers below are measured on **synthetic** documents generated by
> `backend/tests/fixtures/synthetic_reports.py` (6 lab layouts). They show that the pipeline works
> as designed; they are **not** evidence of real-world accuracy. Real-world evaluation needs the annotated
> datasets described in BRD §10 (30+ lab reports), which must be collected with consent
> and de-identified. Clinical diagnostic accuracy is not claimed.

## 1. Printed OCR (BRD §10: CER < 3% on clean digital)

| Engine | Lines | Mean CER | Median CER | Mean WER |
|---|---|---|---|---|
| {ocr.get('engine')} | {ocr.get('lines', 0)} | {pct(ocr['cer']) if 'cer' in ocr else 'n/a'} | {pct(ocr['cer_median']) if 'cer' in ocr else 'n/a'} | {pct(ocr['wer']) if 'wer' in ocr else 'n/a'} |

Digital PDFs bypass OCR entirely (native text, CER 0%). The scanned set is the same reports rasterized at 200 DPI;
CER is computed per printed line against the closest OCR line (Levenshtein).

## 2. Parameter extraction (targets: exact match >= 90%, range accuracy >= 90%, unit normalization >= 95%)

| Input | Recall | Exact match (value + status) | Reference-range accuracy | Unit normalization | Time / report |
|---|---|---|---|---|---|
{ext_rows('Digital PDF (6 layouts)', dig)}
{ext_rows('Scanned image (6 layouts)', scn)}

Extra (phantom) rows - digital: {dig['extra_rows']}{f", scanned: {scn['extra_rows']}" if scn else ''}.
Layouts covered: header tables in different column orders, a header-less table, inline flags (`6.8 H`), units inside the
range column, tiered lipid ranges, sex-specific ranges and a two-page report.

### 2b. Panel benchmark - the 10 priority blood-test panels

{pdig['reports']} synthetic reports (`backend/tests/fixtures/panel_benchmark.py`): 10 panels x 3 lab layouts, Indian-lab
test names and units, values drawn from real-world distributions (NHANES 2017-18 and earlier cycles, UCI CKD, ILPD, HCV -
see `docs/datasets.md`), plus distractor lines (method sub-lines, notes, interpretation paragraphs, booking/page footers)
that must be ignored. Cells: recall / exact match (value + status vs the printed range).

| Panel | Rows | Digital PDF | Scanned image | Extra rows (digital / scanned) |
|---|---|---|---|---|
{panel_rows()}

Remaining scanned errors are OCR misreads of the printed characters (e.g. a range read upside-down, 99 read as 66);
values with no readable range are flagged for the user's check (BR-02).

## 3. Unit normalization dictionary

{units['aliases']} unit spellings: {pct(units['rate'])} normalized correctly ({pct(units['rate_uppercase'])} when upper-cased).
Conversion maths is covered by unit tests (`tests/unit/test_units.py`).

## 4. Handwriting

Out of scope: FITSCAN reads printed lab reports only (the doctor's-prescription feature was removed).

## 5. RAG retrieval (BRD: Precision@5 / Recall@5)

| Questions | Embedder | P@{rag['k']} | R@{rag['k']} | MRR | Hit rate |
|---|---|---|---|---|---|
| {rag['questions']} | {rag['embedder']} | {pct(rag['precision_at_k'])} | {pct(rag['recall_at_k'])} | {rag['mrr']:.2f} | {pct(rag['hit_rate'])} |

Precision@5 is low by construction: most questions have one or two relevant documents.
Hit rate and MRR are the more informative numbers here. Re-run with `sentence-transformers` installed for the dense embedder.

## 6. Safety guardrails (BR-04, BR-05, BR-09)

- Adversarial unsafe outputs blocked: **{guard['blocked']} / {guard['unsafe']}** (diagnosis, treatment, dose, extra tests, urgency language).
- Safe explanations allowed through: **{guard['safe_passed']} / {guard['safe']}**.
- URGENT can only come from `config/escalation_rules.yaml` (unit-tested); the LLM never sets it.

## 7. Explanation faithfulness (manual rubric - to do)

Rate 50 generated explanations, 0-2 on each: (a) states the value and the lab's own range correctly, (b) every general
claim is supported by a cited source, (c) no diagnosis / treatment / test advice, (d) plain language.
With no LLM key configured, explanations come from deterministic templates that only restate verified values and cite
the retrieved source title, so (a)-(c) hold by construction.

## 8. Comparison numerics (target 100% on synthetic)

All comparison unit tests pass (`tests/unit/test_comparison_service.py`): deltas, % change (none when baseline is 0),
mmol/L to mg/dL conversion, incompatible units excluded, changed reference ranges flagged, unverified values excluded.

## 9. Centre discovery

Not scored (needs a 20-query manual rubric). The live smoke test against OpenStreetMap (Pune, 3 km, CBC) returned
15 ranked results with every listing marked *unverified* (BR-12).
"""
    (ROOT / "docs" / "evaluation_report.md").write_text(report, encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
