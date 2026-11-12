"""Shared pipeline schemas (NFR-09).

Pipelines are pure: bytes / Pydantic in -> Pydantic out. No DB access inside stages.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

StageCallback = Callable[[str], None]  # receives a DocumentStatus value when a stage starts


class BBox(BaseModel):
    """Bounding box normalized to the page (0..1) so the UI can overlay it at any zoom."""

    page: int
    x0: float
    y0: float
    x1: float
    y1: float

    @staticmethod
    def union(boxes: list["BBox"]) -> "BBox | None":
        if not boxes:
            return None
        return BBox(
            page=boxes[0].page,
            x0=min(b.x0 for b in boxes), y0=min(b.y0 for b in boxes),
            x1=max(b.x1 for b in boxes), y1=max(b.y1 for b in boxes),
        )


class Word(BaseModel):
    text: str
    conf: float
    bbox: BBox

    @property
    def yc(self) -> float:
        return (self.bbox.y0 + self.bbox.y1) / 2

    @property
    def height(self) -> float:
        return self.bbox.y1 - self.bbox.y0


class LoadedPage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    page_no: int
    width: float
    height: float
    words: list[Word] = Field(default_factory=list)
    source: str = "native"  # native | ocr
    image_cover: float = 0.0  # share of the page covered by pictures (a results table pasted in as an image)
    image: Any = Field(default=None, exclude=True)  # np.ndarray (BGR) when rasterized


class LoadedDocument(BaseModel):
    pages: list[LoadedPage]
    is_digital: bool
    engine: str = "pymupdf"


class MetadataField(BaseModel):
    value: str | None = None
    confidence: float = 0.0
