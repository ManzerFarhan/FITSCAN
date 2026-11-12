"""Printed-text OCR (FR-LAB-3).

Engine preference: PaddleOCR -> RapidOCR (PP-OCR models on ONNX Runtime) -> Tesseract.
Each returns text segments with confidence and a page-normalized bounding box.
"""
from __future__ import annotations

import os
import queue
import shutil
import threading
import unicodedata
from functools import lru_cache

import numpy as np

from app.core.logging import get_logger
from app.pipelines.base import BBox, Word

log = get_logger("ocr")


class OCRUnavailable(RuntimeError):
    pass


def _box_from_points(points, page: int, w: int, h: int) -> BBox:
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    return BBox(page=page, x0=min(xs) / w, y0=min(ys) / h, x1=max(xs) / w, y1=max(ys) / h)


# Per engine; ONNX's default (all logical cores) was ~2x slower on hybrid desktop CPUs. Small hosts: OCR_THREADS=1.
ONNX_THREADS = int(os.environ.get("OCR_THREADS", "4"))
# RapidOCR engines kept for OCR-ing several pages at once (engines are not shared across threads). Each needs ~150 MB;
# 512 MB hosts: OCR_POOL_SIZE=1.
POOL_SIZE = max(1, int(os.environ.get("OCR_POOL_SIZE", "3")))
# Longest side used for text *detection* only (0 = RapidOCR's own choice, up to 2000 px). 512 MB hosts: 960.
DET_MAX_SIDE = int(os.environ.get("OCR_DET_MAX_SIDE", "0"))


def _release_memory() -> None:
    """Hand freed heap back to the OS after a page (Linux/glibc). Without this a 512 MB host keeps ~100 MB of the
    previous page's OCR buffers resident, and the next page's peak lands on top of it."""
    try:
        import ctypes

        ctypes.CDLL("libc.so.6").malloc_trim(0)
    except (OSError, AttributeError):
        pass  # not glibc (Windows/macOS/musl): nothing to do


STRIP_OVERLAP = 120  # px; taller than any printed line, so every line lies whole inside at least one strip


def _rapidocr_strips(engine, image: np.ndarray, page_no: int) -> list[Word]:
    """RapidOCR over the page. With DET_MAX_SIDE set (small hosts) a tall page is read in overlapping horizontal
    strips about half the page width high: detection then sees small print ~1.4x larger than on a whole-page pass
    (960 px for a whole A4 page misses 9 pt text) while using *less* memory per pass. Lines cut by a strip edge are
    dropped there and kept from the neighbouring strip, where they are whole; overlap duplicates are removed."""
    h, w = image.shape[:2]
    strip = max(600, w // 2)
    if not DET_MAX_SIDE or h <= strip * 1.3:
        strip = h
    words: list[Word] = []
    top = 0
    while True:
        bottom = min(h, top + strip)
        # Printed reports are deskewed upstream; the 180-degree angle classifier costs ~1/3 of the time for no gain.
        result, _ = engine(image[top:bottom], use_cls=False)
        for pts, text, conf in result or []:
            ys = [float(p[1]) for p in pts]
            if (top > 0 and min(ys) <= 2) or (bottom < h and max(ys) >= bottom - top - 3):
                continue  # cut by this strip's edge
            text = _clean(text)
            box = _box_from_points([(p[0], float(p[1]) + top) for p in pts], page_no, w, h)
            if text and not any(_iou(o.bbox, box) > 0.4 for o in words):  # same spot read in both strips
                words.append(Word(text=text, conf=float(conf), bbox=box))
        if bottom >= h:
            return words
        top = bottom - STRIP_OVERLAP


_CJK_PUNCT = str.maketrans({"。": ".", "，": ",", "、": ",", "：": ":", "；": ";", "（": "(", "）": ")", "－": "-", "～": "-"})


def _clean(text: str) -> str:
    """PP-OCR models are Chinese+English: map full-width / CJK punctuation they sometimes emit to ASCII."""
    return unicodedata.normalize("NFKC", text).translate(_CJK_PUNCT).strip()


def _iou(a: BBox, b: BBox) -> float:
    ix = max(0.0, min(a.x1, b.x1) - max(a.x0, b.x0))
    iy = max(0.0, min(a.y1, b.y1) - max(a.y0, b.y0))
    inter = ix * iy
    union = (a.x1 - a.x0) * (a.y1 - a.y0) + (b.x1 - b.x0) * (b.y1 - b.y0) - inter
    return inter / union if union > 0 else 0.0


def _new_rapidocr():
    from rapidocr_onnxruntime import RapidOCR  # type: ignore

    engine = RapidOCR(intra_op_num_threads=ONNX_THREADS, inter_op_num_threads=1)
    if DET_MAX_SIDE:
        # Text *detection* runs on a copy shrunk to DET_MAX_SIDE (PP-OCR's own default is 960); boxes are mapped back
        # and *recognition* still reads crops of the full-resolution page. RapidOCR otherwise detects at up to 2000 px,
        # whose activations alone exceed a 512 MB host.
        from rapidocr_onnxruntime.ch_ppocr_det.utils import DetPreProcess  # type: ignore

        det = engine.text_det
        det.get_preprocess = lambda _max_wh: DetPreProcess(DET_MAX_SIDE, "max", det.mean, det.std)
    return engine


class PrintedOCR:
    def __init__(self) -> None:
        self.engine_name, self._engine = self._init_engine()
        self._pool: queue.Queue = queue.Queue()
        self._created = 1
        self._lock = threading.Lock()
        if self._engine is not None:
            self._pool.put(self._engine)

    @staticmethod
    def _init_engine():
        try:
            from paddleocr import PaddleOCR  # type: ignore

            return "paddleocr", PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
        except Exception:
            pass
        try:
            return "rapidocr", _new_rapidocr()
        except Exception:
            pass
        try:
            import pytesseract  # type: ignore

            if shutil.which("tesseract"):
                return "tesseract", pytesseract
        except Exception:
            pass
        return "none", None

    @property
    def available(self) -> bool:
        return self._engine is not None

    @property
    def parallel_pages(self) -> int:
        return POOL_SIZE if self.engine_name == "rapidocr" else 1

    def _acquire(self):
        try:
            return self._pool.get_nowait()
        except queue.Empty:
            pass
        with self._lock:
            if self.engine_name == "rapidocr" and self._created < POOL_SIZE:
                self._created += 1
                return _new_rapidocr()
        return self._pool.get()

    def run(self, image: np.ndarray, page_no: int) -> list[Word]:
        if self._engine is None:
            raise OCRUnavailable("No OCR engine installed (PaddleOCR / RapidOCR / Tesseract).")
        engine = self._acquire()
        try:
            return self._run(engine, image, page_no)
        finally:
            self._pool.put(engine)
            _release_memory()

    def _run(self, engine, image: np.ndarray, page_no: int) -> list[Word]:
        h, w = image.shape[:2]
        words: list[Word] = []
        if self.engine_name == "paddleocr":
            result = engine.ocr(image, cls=True) or []
            for line in result[0] or []:
                pts, (text, conf) = line
                words.append(Word(text=text, conf=float(conf), bbox=_box_from_points(pts, page_no, w, h)))
        elif self.engine_name == "rapidocr":
            words = _rapidocr_strips(engine, image, page_no)
        else:
            d = engine.image_to_data(image, output_type=engine.Output.DICT)
            for i, text in enumerate(d["text"]):
                conf = float(d["conf"][i])
                if text.strip() and conf >= 0:
                    x, y, bw, bh = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
                    words.append(Word(text=text, conf=conf / 100,
                                      bbox=BBox(page=page_no, x0=x / w, y0=y / h, x1=(x + bw) / w, y1=(y + bh) / h)))
        return [wd for wd in words if wd.text.strip()]


@lru_cache
def get_printed_ocr() -> PrintedOCR:
    ocr = PrintedOCR()
    log.info("Printed OCR engine: %s", ocr.engine_name)
    return ocr
