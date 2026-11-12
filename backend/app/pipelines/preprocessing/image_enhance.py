"""Image enhancement for OCR (FR-LAB-1): upscale small images, denoise, contrast (CLAHE), deskew."""
from __future__ import annotations

import os

import cv2
import numpy as np

# Small hosts: CV_THREADS=1. OpenCV otherwise starts one worker per *host* core (with per-thread buffers), even when
# the container only gets a fraction of one CPU - enough to push a 512 MB instance over its memory limit.
if os.environ.get("CV_THREADS"):
    cv2.setNumThreads(int(os.environ["CV_THREADS"]))

MIN_LONG_SIDE = 1600
MAX_LONG_SIDE = 3500


def _resize(gray: np.ndarray) -> np.ndarray:
    h, w = gray.shape[:2]
    long_side = max(h, w)
    if long_side < MIN_LONG_SIDE:
        s = MIN_LONG_SIDE / long_side
        return cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    if long_side > MAX_LONG_SIDE:
        s = MAX_LONG_SIDE / long_side
        return cv2.resize(gray, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return gray


def estimate_skew(gray: np.ndarray) -> float:
    """Skew angle in degrees (positive = counter-clockwise), from text-pixel min-area rectangle."""
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    coords = np.column_stack(np.where(bw > 0))
    if len(coords) < 500:
        return 0.0
    angle = cv2.minAreaRect(coords[:, ::-1].astype(np.float32))[-1]
    if angle > 45:
        angle -= 90
    return float(angle)


def deskew(gray: np.ndarray, max_angle: float = 15.0) -> np.ndarray:
    angle = estimate_skew(gray)
    if abs(angle) < 0.5 or abs(angle) > max_angle:
        return gray
    h, w = gray.shape[:2]
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    return cv2.warpAffine(gray, m, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


def enhance(image: np.ndarray) -> np.ndarray:
    """BGR/gray in -> enhanced BGR out (same scale as input is NOT guaranteed)."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    gray = _resize(gray)
    gray = cv2.fastNlMeansDenoising(gray, None, h=7, templateWindowSize=7, searchWindowSize=15)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    gray = clahe.apply(gray)
    gray = deskew(gray)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
