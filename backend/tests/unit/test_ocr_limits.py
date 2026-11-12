"""OCR_MAX_SIDE shrinks big pages before OCR (memory cap for small hosts); boxes stay page-normalised."""
import numpy as np


def test_fit_caps_longest_side(monkeypatch):
    from app.pipelines.ocr import printed_ocr as p

    page = np.zeros((2339, 1654, 3), np.uint8)
    monkeypatch.setattr(p, "MAX_SIDE", 0)
    assert p._fit(page) is page  # default: untouched
    monkeypatch.setattr(p, "MAX_SIDE", 1600)
    small = p._fit(page)
    assert small.shape[:2] == (1600, 1131)
    tiny = np.zeros((500, 400, 3), np.uint8)
    assert p._fit(tiny) is tiny  # never upscales


def test_detection_side_cap(monkeypatch):
    import pytest

    pytest.importorskip("rapidocr_onnxruntime")
    from app.pipelines.ocr import printed_ocr as p

    monkeypatch.setattr(p, "DET_MAX_SIDE", 960)
    det = p._new_rapidocr().text_det
    op = det.get_preprocess(2339)  # an A4 page at 200 dpi
    assert (op.limit_side_len, op.limit_type) == (960, "max")
