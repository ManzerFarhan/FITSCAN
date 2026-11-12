"""PDF / image loading (FR-LAB-1). Digital PDFs: native text first; scanned pages are rasterized for OCR."""
from __future__ import annotations

import numpy as np
import pymupdf as fitz

from app.pipelines.base import BBox, LoadedDocument, LoadedPage, Word

NATIVE_TEXT_MIN_WORDS = 15
RENDER_DPI = 220


class PageLimitExceeded(Exception):
    pass


def count_pdf_pages(data: bytes) -> int:
    with fitz.open(stream=data, filetype="pdf") as doc:
        return doc.page_count


def render_page_png(data: bytes, mime: str, page_no: int, dpi: int = 110) -> bytes:
    """Render one page as PNG for preview / verification crops."""
    if mime == "application/pdf":
        with fitz.open(stream=data, filetype="pdf") as doc:
            page = doc.load_page(page_no - 1)
            return page.get_pixmap(dpi=dpi).tobytes("png")
    with fitz.open(stream=data, filetype=mime.split("/")[-1]) as doc:
        return doc.load_page(0).get_pixmap().tobytes("png")


def _pix_to_bgr(pix: "fitz.Pixmap") -> np.ndarray:
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    if pix.n == 4:
        arr = arr[:, :, :3]
    elif pix.n == 1:
        arr = np.repeat(arr, 3, axis=2)
    return arr[:, :, ::-1].copy()  # RGB -> BGR


def _native_words(page: "fitz.Page", page_no: int) -> list[Word]:
    w, h = page.rect.width, page.rect.height
    words = []
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        if text.strip():
            words.append(Word(text=text, conf=0.99, bbox=BBox(page=page_no, x0=x0 / w, y0=y0 / h, x1=x1 / w, y1=y1 / h)))
    return words


def load_document(data: bytes, mime: str, max_pages: int = 30) -> LoadedDocument:
    if mime == "application/pdf":
        pages: list[LoadedPage] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.page_count > max_pages:
                raise PageLimitExceeded(f"PDF has {doc.page_count} pages; limit is {max_pages}.")
            for i, page in enumerate(doc, start=1):
                words = _native_words(page, i)
                if len(words) >= NATIVE_TEXT_MIN_WORDS:
                    pages.append(LoadedPage(page_no=i, width=page.rect.width, height=page.rect.height, words=words, source="native"))
                else:
                    pix = page.get_pixmap(dpi=RENDER_DPI)
                    pages.append(LoadedPage(page_no=i, width=pix.width, height=pix.height, source="ocr", image=_pix_to_bgr(pix)))
        return LoadedDocument(pages=pages, is_digital=all(p.source == "native" for p in pages))

    import cv2

    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")
    h, w = img.shape[:2]
    return LoadedDocument(pages=[LoadedPage(page_no=1, width=w, height=h, source="ocr", image=img)], is_digital=False)
