"""Layout helpers shared by pipelines: group words into lines, lines into cells."""
from __future__ import annotations

import statistics

from pydantic import BaseModel

from app.pipelines.base import BBox, Word


class Cell(BaseModel):
    text: str
    conf: float
    bbox: BBox

    @property
    def xc(self) -> float:
        return (self.bbox.x0 + self.bbox.x1) / 2


class Line(BaseModel):
    page: int
    words: list[Word]
    cells: list[Cell] = []

    @property
    def text(self) -> str:
        return " ".join(w.text for w in self.words)

    @property
    def bbox(self) -> BBox:
        return BBox.union([w.bbox for w in self.words])  # type: ignore[return-value]

    @property
    def conf(self) -> float:
        return min(w.conf for w in self.words) if self.words else 0.0


def group_lines(words: list[Word]) -> list[Line]:
    """Cluster words into text lines by vertical overlap, per page, top-to-bottom."""
    lines: list[Line] = []
    by_page: dict[int, list[Word]] = {}
    for w in words:
        by_page.setdefault(w.bbox.page, []).append(w)
    for page in sorted(by_page):
        ws = sorted(by_page[page], key=lambda w: (w.yc, w.bbox.x0))
        if not ws:
            continue
        med_h = statistics.median(w.height for w in ws) or 0.01
        current: list[Word] = []
        current_yc = None
        for w in ws:
            if current and abs(w.yc - current_yc) > 0.55 * med_h:
                lines.append(Line(page=page, words=sorted(current, key=lambda x: x.bbox.x0)))
                current = []
            current.append(w)
            current_yc = statistics.mean(x.yc for x in current)
        if current:
            lines.append(Line(page=page, words=sorted(current, key=lambda x: x.bbox.x0)))
    for line in lines:
        line.cells = split_cells(line.words)
    return lines


def split_cells(words: list[Word], gap_factor: float = 1.1) -> list[Cell]:
    """Merge horizontally-adjacent words into cells; a wide gap starts a new cell (column)."""
    if not words:
        return []
    med_h = statistics.median(w.height for w in words) or 0.01
    cells: list[list[Word]] = [[words[0]]]
    for prev, w in zip(words, words[1:]):
        gap = w.bbox.x0 - prev.bbox.x1
        if gap > gap_factor * med_h:
            cells.append([w])
        else:
            cells[-1].append(w)
    return [
        Cell(text=" ".join(w.text for w in c), conf=min(w.conf for w in c), bbox=BBox.union([w.bbox for w in c]))  # type: ignore[arg-type]
        for c in cells
    ]
