"""Printed-text OCR (FR-LAB-3).

Engine preference: PaddleOCR -> RapidOCR (PP-OCR models on ONNX Runtime) -> Tesseract.
Each returns text segments with confidence and a page-normalized bounding box.
"""
from __future__ import annotations

import os
import queue
import shutil
import threading
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
# Longest page side fed to OCR (0 = no limit). Detection memory grows with page area; 512 MB hosts: OCR_MAX_SIDE=1600.
MAX_SIDE = int(os.environ.get("OCR_MAX_SIDE", "0"))


def _fit(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[:2]
    if not MAX_SIDE or max(h, w) <= MAX_SIDE:
        return image
    import cv2

    scale = MAX_SIDE / max(h, w)
    return cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)


def _new_rapidocr():
    from rapidocr_onnxruntime import RapidOCR  # type: ignore

    return RapidOCR(intra_op_num_threads=ONNX_THREADS, inter_op_num_threads=1)


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
            return self._run(engine, _fit(image), page_no)  # boxes are page-normalised, so scaling is transparent
        finally:
            self._pool.put(engine)

    def _run(self, engine, image: np.ndarray, page_no: int) -> list[Word]:
        h, w = image.shape[:2]
        words: list[Word] = []
        if self.engine_name == "paddleocr":
            result = engine.ocr(image, cls=True) or []
            for line in result[0] or []:
                pts, (text, conf) = line
                words.append(Word(text=text, conf=float(conf), bbox=_box_from_points(pts, page_no, w, h)))
        elif self.engine_name == "rapidocr":
            # Printed reports are deskewed upstream; the 180-degree angle classifier costs ~1/3 of the time for no gain.
            result, _ = engine(image, use_cls=False)
            for pts, text, conf in result or []:
                words.append(Word(text=text, conf=float(conf), bbox=_box_from_points(pts, page_no, w, h)))
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
