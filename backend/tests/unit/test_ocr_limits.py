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
