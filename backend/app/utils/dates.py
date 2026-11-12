"""Date parsing for Indian-format documents (day-first, A6/A7)."""
from __future__ import annotations

import re
from datetime import date, datetime

_MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], start=1)}

DATE_PATTERN = (
    r"(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}"                       # 2024-03-12
    r"|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}"                    # 12/03/2024, 12-03-24
    r"|\d{1,2}[\s\-/.]*[A-Za-z]{3,9}[\s\-/.,]*\d{2,4}"     # 12 Mar 2024, 12-Mar-2024
    r"|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4})"                 # March 12, 2024
)


def _year(y: int) -> int:
    return y + 2000 if y < 100 else y


def parse_date(text: str | None) -> date | None:
    if not text:
        return None
    t = text.strip()
    try:
        m = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", t)
        if m:
            return date(int(m[1]), int(m[2]), int(m[3]))
        m = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", t)
        if m:
            return date(_year(int(m[3])), int(m[2]), int(m[1]))
        m = re.fullmatch(r"(\d{1,2})[\s\-/.]*([A-Za-z]{3,9})[\s\-/.,]*(\d{2,4})", t)
        if m and m[2][:3].lower() in _MONTHS:
            return date(_year(int(m[3])), _MONTHS[m[2][:3].lower()], int(m[1]))
        m = re.fullmatch(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", t)
        if m and m[1][:3].lower() in _MONTHS:
            return date(int(m[3]), _MONTHS[m[1][:3].lower()], int(m[2]))
    except ValueError:
        return None
    return None


def find_date(text: str) -> date | None:
    for m in re.finditer(DATE_PATTERN, text):
        d = parse_date(m.group(1))
        if d and 1950 <= d.year <= datetime.now().year + 1:
            return d
    return None
