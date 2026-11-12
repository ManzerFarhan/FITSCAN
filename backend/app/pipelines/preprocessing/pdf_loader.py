"""PDF / image loading (FR-LAB-1).

Each PDF page is read from its own text when that text can be trusted, otherwise it is OCR'd:
- invisible text (a scanner's built-in OCR layer, often poor or header-only) is never trusted;
- garbled text (fonts without a Unicode map) is never trusted;
- rotated pages are mapped to how they are displayed;
- pages that are mostly a picture keep their text but are flagged (`image_cover`) so the pipeline can OCR them
  when that text holds no results table (header as text, results pasted in as an image).
Pages are rendered for OCR lazily, one at a time (`render_page_bgr`), to keep memory low.
"""
from __future__ import annotations

import re

import numpy as np
import pymupdf as fitz

from app.pipelines.base import BBox, LoadedDocument, LoadedPage, Word

NATIVE_TEXT_MIN_WORDS = 15
RENDER_DPI = 220
_READABLE = re.compile(r"[A-Za-z0-9\s.,:;()\[\]/%<>=+\-*#&'\"µμ°^|_]")


class PageLimitExceeded(Exception):
    pass


def count_pdf_pages(data: bytes) -> int:
    with fitz.open(stream=data, filetype="pdf") as doc:
        return doc.page_count


def render_page_png(data: bytes, mime: str, page_no: int, dpi: int = 110) -> bytes:
    """Render one page as PNG for preview / verification crops."""
    if mime == "application/pdf":
        with fitz.open(stream=data, filetype="pdf") as doc:
            return doc.load_page(page_no - 1).get_pixmap(dpi=dpi).tobytes("png")
    with fitz.open(stream=data, filetype=mime.split("/")[-1]) as doc:
        return doc.load_page(0).get_pixmap().tobytes("png")


def render_page_bgr(data: bytes, page_no: int, dpi: int = RENDER_DPI) -> np.ndarray:
    """One PDF page as a BGR image for OCR (as displayed, i.e. rotation applied)."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        pix = doc.load_page(page_no - 1).get_pixmap(dpi=dpi)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    arr = arr[:, :, :3] if pix.n == 4 else np.repeat(arr, 3, axis=2) if pix.n == 1 else arr
    return arr[:, :, ::-1].copy()  # RGB -> BGR


def _trusted_words(page: "fitz.Page", page_no: int) -> list[Word]:
    """The page's own text, in display coordinates - or [] when it can't be trusted."""
    visible = invisible = 0
    for span in page.get_texttrace():
        if span["type"] == 3:  # render mode 3 = invisible (a scanner's OCR layer)
            invisible += len(span["chars"])
        else:
            visible += len(span["chars"])
    if visible < invisible:
        return []
    raw = page.get_text("words")
    text = "".join(w[4] for w in raw)
    if text and len(_READABLE.findall(text)) / len(text) < 0.8:  # garbled: fonts without a Unicode map
        return []
    w, h, m = page.rect.width, page.rect.height, page.rotation_matrix
    words = []
    for x0, y0, x1, y1, t, *_ in raw:
        if t.strip():
            r = fitz.Rect(x0, y0, x1, y1) * m  # unrotated -> displayed coordinates
            words.append(Word(text=t, conf=0.99, bbox=BBox(page=page_no, x0=r.x0 / w, y0=r.y0 / h, x1=r.x1 / w, y1=r.y1 / h)))
    return words


def _image_cover(page: "fitz.Page") -> float:
    area = page.rect.get_area() or 1.0
    return min(1.0, sum((fitz.Rect(i["bbox"]) & page.rect).get_area() for i in page.get_image_info()) / area)


def load_document(data: bytes, mime: str, max_pages: int = 30) -> LoadedDocument:
    if mime == "application/pdf":
        pages: list[LoadedPage] = []
        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.page_count > max_pages:
                raise PageLimitExceeded(f"PDF has {doc.page_count} pages; limit is {max_pages}.")
            for i, page in enumerate(doc, start=1):
                words = _trusted_words(page, i)
                native = len(words) >= NATIVE_TEXT_MIN_WORDS
                pages.append(LoadedPage(page_no=i, width=page.rect.width, height=page.rect.height,
                                        words=words if native else [], source="native" if native else "ocr",
                                        image_cover=_image_cover(page)))
        return LoadedDocument(pages=pages, is_digital=all(p.source == "native" for p in pages))

    import cv2

    img = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image.")
    h, w = img.shape[:2]
    return LoadedDocument(pages=[LoadedPage(page_no=1, width=w, height=h, source="ocr", image=img, image_cover=1.0)],
                          is_digital=False)
