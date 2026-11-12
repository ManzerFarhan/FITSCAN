"""Regression gate for the 10 priority panels (digital PDFs; the scanned run lives in evaluation/run_eval.py).
Synthetic reports only - values sampled from aggregate real-world statistics, never real rows."""
from app.pipelines.lab_report.pipeline import LabReportPipeline
from tests.fixtures.panel_benchmark import PANELS, SPEC, build_reports
from tests.fixtures.synthetic_reports import render_pdf


def test_every_benchmark_name_is_in_the_dictionary():
    from app.pipelines.lab_report.normalizer import match_parameter

    for pid, (names, _, _) in SPEC.items():
        for n in names:
            assert match_parameter(n).parameter_id == pid, n


def test_panel_benchmark_digital():
    reports = build_reports()
    assert len(reports) == len(PANELS) * 3
    rows = found = exact = extra = 0
    for lo in reports:
        res = LabReportPipeline().run(render_pdf(lo), "application/pdf")
        got = {p.parameter_id: p for p in res.parameters if p.parameter_id}
        ids = {e.parameter_id for e in lo.expected}
        extra += sum(1 for p in res.parameters if p.parameter_id not in ids)  # notes/footers must never become rows
        for e in lo.expected:
            rows += 1
            p = got.get(e.parameter_id)
            found += p is not None
            exact += bool(p and p.value_num == e.value and p.status == e.status
                          and (p.ref_low, p.ref_high) == (e.ref_low, e.ref_high))
    assert rows >= 140
    assert extra == 0
    assert found == rows
    assert exact / rows >= 0.99
