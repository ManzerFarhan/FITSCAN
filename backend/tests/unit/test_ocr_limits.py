"""OCR_DET_MAX_SIDE caps only text *detection* size (memory on small hosts); recognition stays full-res."""
import pytest


def test_detection_side_cap(monkeypatch):
    pytest.importorskip("rapidocr_onnxruntime")
    from app.pipelines.ocr import printed_ocr as p

    monkeypatch.setattr(p, "DET_MAX_SIDE", 960)
    det = p._new_rapidocr().text_det
    op = det.get_preprocess(2339)  # an A4 page at 200 dpi
    assert (op.limit_side_len, op.limit_type) == (960, "max")
