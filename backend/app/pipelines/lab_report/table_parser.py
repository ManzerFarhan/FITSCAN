"""Layout-agnostic lab table parsing (FR-LAB-4). No per-lab templates.

Each text line is split into cells (by horizontal gaps). Cells are classified by *content*
(numeric value, reference range, unit, flag, name); when a header row is found, column
positions are used to disambiguate (e.g. an unknown unit string sitting in the Unit column).
Works across pages; each page's header is detected independently.
"""
from __future__ import annotations

import re

from pydantic import BaseModel

from app.pipelines.base import BBox
from app.pipelines.lab_report.range_parser import parse_range
from app.pipelines.layout import Cell, Line
from app.utils import dictionaries

_VALUE_RE = re.compile(r"^[<>]?\s*-?\d{1,3}(?:,\d{2,3})*(?:\.\d+)?$|^[<>]?\s*-?\d+(?:\.\d+)?$")
_FLAG_RE = re.compile(r"^(?:\*?H\*?|\*?L\*?|HH|LL|\*{1,2}|HIGH|LOW|↑|↓)$", re.IGNORECASE)
_VALUE_FLAG_RE = re.compile(r"^([<>]?\s*\d[\d,]*(?:\.\d+)?)\s*(\*?H\*?|\*?L\*?|HH|LL|\*{1,2}|HIGH|LOW)$", re.IGNORECASE)
_FLAG_VALUE_RE = re.compile(r"^(H|L|HH|LL|HIGH|LOW)\s+([<>]?\d[\d,]*(?:\.\d+)?)$", re.IGNORECASE)
_VALUE_UNIT_RE = re.compile(r"^([<>]?\d[\d,]*(?:\.\d+)?)\s+([a-zA-Zµμ%/^\d.]+(?:\s*/\s*[a-zA-Zµμ\d.]+)*)$")
_UNIT_SHAPE_RE = re.compile(r"^(?:[a-zA-Zµμ%^\d.*x]+\s*/\s*[a-zA-Zµμ\d.^ ]+|%|fl|fL|pg|ratio|mm/hr|g%|mg%)$", re.IGNORECASE)
_HEADER_WORDS = {
    "name": {"test", "tests", "investigation", "investigations", "parameter", "parameters", "test name", "description", "examination"},
    "value": {"result", "results", "value", "observed value", "observed", "observation", "your value", "patient value"},
    "unit": {"unit", "units", "uom"},
    "range": {"reference", "reference range", "ref range", "range", "normal range", "biological reference interval",
              "bio ref interval", "reference interval", "normal value", "normal values", "ref. range", "biological ref. interval"},
    "flag": {"flag", "flags", "status", "remarks"},
}


class RawRow(BaseModel):
    name_raw: str
    value_raw: str | None = None
    unit_raw: str | None = None
    ref_raw: str | None = None
    flag_raw: str | None = None
    conf: float
    bbox: BBox
    page_no: int
    ambiguous: bool = False
    line_text: str = ""  # the whole printed line - lets callers spot notes/footers that span the columns


def _is_value(t: str) -> bool:
    return bool(_VALUE_RE.match(t.strip()))


def _is_range(t: str) -> bool:
    s = t.strip()
    if not re.search(r"\d", s):
        return False
    r = parse_range(s)
    if r.kind in ("between", "sex_specific"):
        return True
    if r.kind in ("upper", "lower"):
        return True
    return bool(re.search(r"\b(?:normal|desirable|optimal|male|female)\b", s, re.IGNORECASE))


def _is_unit(t: str) -> bool:
    s = t.strip()
    if not s or len(s) > 20:
        return False
    aliases = dictionaries.unit_conversions()["aliases"]
    key = re.sub(r"\s*/\s*", "/", s.lower().replace("μ", "µ"))
    return key in aliases or key.replace(" ", "") in aliases or bool(_UNIT_SHAPE_RE.match(s))


def _has_letters(t: str) -> bool:
    return bool(re.search(r"[A-Za-z]{2,}", t))


def _header_columns(line: Line) -> dict[str, float] | None:
    cols: dict[str, float] = {}
    for c in line.cells:
        key = re.sub(r"[^a-z. ]", "", c.text.lower()).strip()
        for role, words in _HEADER_WORDS.items():
            if key in words or any(key.startswith(w) for w in words if len(w) > 4):
                cols.setdefault(role, c.xc)
    if "value" in cols and ("range" in cols or "unit" in cols) and len(cols) >= 3:
        return cols
    return None


def _nearest_role(cell: Cell, cols: dict[str, float] | None) -> str | None:
    if not cols:
        return None
    return min(cols.items(), key=lambda kv: abs(kv[1] - cell.xc))[0]


_GLUED_RANGE_RE = re.compile(r"^(\S+?)([<>]=?\s*\d[\d.,]*)$")  # split only when the left part is a known unit


def _split_glued_ranges(cells: list[Cell]) -> list[Cell]:
    """OCR can glue a unit to a one-sided range: 'mL/min/1.73m2>90' -> 'mL/min/1.73m2', '>90'."""
    out: list[Cell] = []
    for c in cells:
        m = _GLUED_RANGE_RE.match(c.text.strip())
        if m and _is_unit(m.group(1)):
            out += [Cell(text=m.group(1), conf=c.conf, bbox=c.bbox), Cell(text=m.group(2), conf=c.conf, bbox=c.bbox)]
        else:
            out.append(c)
    return out


def parse_line(line: Line, cols: dict[str, float] | None) -> RawRow | None:
    cells = line.cells
    if len(cells) < 2:
        # single cell lines may still be "Hemoglobin 13.5 g/dL 13-17" with tight spacing
        cells = [Cell(text=w.text, conf=w.conf, bbox=w.bbox) for w in line.words]
        if len(cells) < 2:
            return None
    cells = _split_glued_ranges(cells)
    # name = leading cells that carry letters and are not values/ranges/units
    name_parts: list[Cell] = []
    i = 0
    # A short leading number that belongs to the name ("25 Hydroxy Vitamin D") or is a serial number ("1 Haemoglobin").
    first = cells[0].text.strip()
    if len(cells) > 2 and re.fullmatch(r"\d{1,3}\.?", first) and _has_letters(cells[1].text):
        name_parts.append(cells[0])
        i = 1
    elif len(cells) > 1 and re.match(r"^\d{1,3}\.?\s+[A-Za-z]{4,}", first) and not _is_unit(first.split(None, 1)[1]):
        name_parts.append(cells[0])  # "25 HydroxyVitaminD" in one cell: a name, not "value + unit"
        i = 1
    while i < len(cells):
        c = cells[i]
        if _has_letters(c.text) and not _is_range(c.text) and not _VALUE_UNIT_RE.match(c.text.strip()) \
                and not (name_parts and _is_unit(c.text)) and not (name_parts and _FLAG_RE.match(c.text.strip())):
            if cols and name_parts and _nearest_role(c, cols) not in ("name", None):
                break
            name_parts.append(c)
            i += 1
        else:
            break
    if not name_parts:
        return None
    name = " ".join(c.text for c in name_parts).strip(" :.-")
    # A trailing value glued to the name ("Hemoglobin 13.5")
    m = re.match(r"^(.*?[A-Za-z)\]])\s+([<>]?\d[\d,]*(?:\.\d+)?)$", name)
    rest = cells[i:]
    value = unit = ref = flag = None
    ambiguous = False
    if m and not rest:
        name, value = m.group(1), m.group(2)

    for c in rest:
        t = c.text.strip()
        role = _nearest_role(c, cols)
        if value is None and _is_value(t) and role in (None, "value", "flag"):
            value = t
            continue
        if value is None and (mv := _VALUE_FLAG_RE.match(t)):
            value, flag = mv.group(1), mv.group(2)
            continue
        if value is None and (mv := _FLAG_VALUE_RE.match(t)):
            flag, value = mv.group(1), mv.group(2)
            continue
        if value is None and (mv := _VALUE_UNIT_RE.match(t)) and _is_unit(mv.group(2)):
            value, unit = mv.group(1), mv.group(2)
            continue
        if flag is None and _FLAG_RE.match(t):
            flag = t
            continue
        if ref is None and _is_range(t):
            # range may carry a unit suffix: "13 - 17 g/dL"
            mu = re.match(r"^(.*\d)\s+([a-zA-Zµμ%/^.\d]+(?:/[a-zA-Zµμ\d.]+)?)$", t)
            if mu and _is_unit(mu.group(2)) and not re.search(r"(?i)up ?to|less|more|than", mu.group(2)):
                ref = mu.group(1)
                unit = unit or mu.group(2)
            else:
                ref = t
            continue
        if unit is None and (_is_unit(t) or role == "unit"):
            unit = t
            continue
        if value is None and role == "value":
            value = t  # non-numeric result (e.g. "Negative") - kept raw
            continue
        if value is not None and _is_value(t) and ref is None:
            ambiguous = True  # two numeric results on one line: which belongs to the name?

    if value is None:
        return None
    # Accept only rows that look like lab results
    if ref is None and unit is None and flag is None:
        return None
    bbox = BBox.union([c.bbox for c in cells])
    return RawRow(
        name_raw=name, value_raw=value, unit_raw=unit, ref_raw=ref, flag_raw=flag,
        conf=min(c.conf for c in cells), bbox=bbox, page_no=line.page, ambiguous=ambiguous,  # type: ignore[arg-type]
        line_text=line.text,
    )


def parse_tables(lines: list[Line]) -> list[RawRow]:
    rows: list[RawRow] = []
    cols: dict[str, float] | None = None
    page = None
    for line in lines:
        if line.page != page:
            page, cols = line.page, None
        header = _header_columns(line)
        if header:
            cols = header
            continue
        row = parse_line(line, cols)
        if row:
            rows.append(row)
    return rows
