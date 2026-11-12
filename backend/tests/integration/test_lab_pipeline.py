"""P2-28: pipeline tests on >=5 synthetic lab layouts (exit criterion of Phase 2)."""
import pytest

from app.pipelines.lab_report.pipeline import LabReportPipeline
from app.utils.units import normalize_unit
from tests.fixtures.synthetic_reports import LAYOUTS, render_pdf, render_png


def _by_pid(result):
    return {p.parameter_id: p for p in result.parameters if p.parameter_id}


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda lo: lo.key)
def test_digital_pdf_layouts(layout):
    result = LabReportPipeline().run(render_pdf(layout), "application/pdf")
    assert result.is_digital
    got = _by_pid(result)
    for exp in layout.expected:
        assert exp.parameter_id in got, f"{layout.key}: missing {exp.parameter_id}; got {list(got)}"
        p = got[exp.parameter_id]
        assert p.value_num == pytest.approx(exp.value), (layout.key, p)
        assert p.ref_low == exp.ref_low and p.ref_high == exp.ref_high, (layout.key, p)
        assert p.status == exp.status, (layout.key, p)
        if exp.unit:
            assert p.unit_normalized == normalize_unit(exp.unit), (layout.key, p)
        if exp.flag:
            assert p.lab_flag == exp.flag
    # no phantom rows from header/metadata lines
    assert len(result.parameters) == len(layout.expected), [p.name_raw for p in result.parameters]


@pytest.mark.parametrize("layout", LAYOUTS, ids=lambda lo: lo.key)
def test_metadata(layout):
    result = LabReportPipeline().run(render_pdf(layout), "application/pdf")
    for key, value in layout.meta.items():
        assert key in result.metadata, f"{layout.key}: missing {key}"
        assert result.metadata[key].value == value, (layout.key, key, result.metadata[key])


def test_lab_address_never_patient_address():  # BR-06
    for layout in LAYOUTS:
        result = LabReportPipeline().run(render_pdf(layout), "application/pdf")
        assert "patient_address" not in result.metadata


def test_sex_specific_range_uses_document_sex():
    kft = next(lo for lo in LAYOUTS if lo.key == "lifeline_kft_sexranges")
    result = LabReportPipeline().run(render_pdf(kft), "application/pdf")
    assert result.metadata["patient_sex"].value == "M"
    creat = _by_pid(result)["creatinine"]
    assert (creat.ref_low, creat.ref_high) == (0.7, 1.3)


def test_clean_digital_report_is_high_confidence():
    result = LabReportPipeline().run(render_pdf(LAYOUTS[0]), "application/pdf")
    assert all(not p.needs_verification for p in result.parameters)


def test_implausible_value_is_flagged():
    from app.pipelines.lab_report.pipeline import build_parameter

    p = build_parameter(0, "Haemoglobin", "135", "g/dL", "12-15", None, 0.99, None, 1, 0.85)
    assert "IMPLAUSIBLE_VALUE" in p.issues
    assert p.needs_verification


@pytest.mark.ocr
def test_scanned_image_ocr_path():
    from app.pipelines.ocr.printed_ocr import get_printed_ocr

    if not get_printed_ocr().available:
        pytest.skip("no OCR engine installed")
    layout = LAYOUTS[0]
    result = LabReportPipeline().run(render_png(layout), "image/png")
    assert not result.is_digital
    got = _by_pid(result)
    hits = sum(1 for e in layout.expected if e.parameter_id in got and got[e.parameter_id].value_num == pytest.approx(e.value))
    assert hits >= len(layout.expected) - 1, [(p.name_raw, p.value_raw, p.ref_raw) for p in result.parameters]
