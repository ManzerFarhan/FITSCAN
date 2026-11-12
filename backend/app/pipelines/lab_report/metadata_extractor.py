"""Report metadata extraction (FR-LAB-2). BR-06: lab address is never the patient address."""
from __future__ import annotations

import re
from collections import Counter

from app.pipelines.base import MetadataField
from app.pipelines.layout import Line
from app.utils.dates import DATE_PATTERN, find_date, parse_date

_LAB_WORDS = re.compile(r"\b(?:labs?|laborator(?:y|ies)|diagnostics?|patholog(?:y|ical)|path ?lab|imaging|healthcare|health care|hospital|clinic|medical cent(?:re|er))\b", re.IGNORECASE)
_ADDRESS_HINT = re.compile(r"\b(?:road|rd\.?|street|st\.|nagar|sector|floor|plot|lane|marg|colony|near|opp\.?|building|bldg|phase|block|\d{6})\b", re.IGNORECASE)
_LABEL_END = r"(?=\s{2,}|\s+(?:age|sex|gender|dob|uhid|mrn|id|ref(?:erred)?|patient id|sample|reg|lab|report|date|collected|phone|mobile)\b|$)"


def _search(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip(" :.-,") if m else None


def _date_after(label: str, text: str) -> str | None:
    m = re.search(label + r"\s*(?:date|on)?\s*(?:&\s*time)?\s*[:\-]?\s*" + DATE_PATTERN, text, re.IGNORECASE)
    if not m:
        return None
    d = parse_date(m.group(1))
    return d.isoformat() if d else None


def extract_metadata(lines: list[Line], category_votes: Counter | None = None) -> dict[str, MetadataField]:
    page1 = [ln for ln in lines if ln.page == 1]
    text = "\n".join(ln.text for ln in lines)
    meta: dict[str, MetadataField] = {}

    # Lab name + address: from the header area of page 1
    lab_idx = None
    for i, ln in enumerate(page1[:10]):
        if _LAB_WORDS.search(ln.text) and not re.search(r"(?i)patient|name\s*:", ln.text):
            meta["lab_name"] = MetadataField(value=ln.text.strip(), confidence=round(0.9 * ln.conf, 3))
            lab_idx = i
            break
    if lab_idx is not None:
        addr = [ln.text for ln in page1[lab_idx + 1: lab_idx + 4] if _ADDRESS_HINT.search(ln.text) and not re.search(r"(?i)patient|name\s*:", ln.text)]
        if addr:
            meta["lab_address"] = MetadataField(value=", ".join(addr), confidence=0.75)

    name = _search(r"(?:patient(?:'s)?\s*name|name\s*of\s*(?:the\s*)?patient|pt\.?\s*name|^\s*name)\s*[:\-]\s*((?:mr|mrs|ms|miss|master|baby)?\.?\s*[A-Za-z][A-Za-z .']{1,60}?)" + _LABEL_END, text)
    if name:
        meta["patient_name"] = MetadataField(value=re.sub(r"\s+", " ", name), confidence=0.85)

    sex = _search(r"(?:sex|gender)\s*[:\-]?\s*(male|female|m|f)\b", text) or _search(r"age\s*/\s*(?:sex|gender)\s*[:\-]?\s*\d+\s*(?:y(?:ea)?rs?|y)?\s*/\s*(male|female|m|f)\b", text)
    if sex:
        meta["patient_sex"] = MetadataField(value=sex[0].upper(), confidence=0.9)

    # BR-06: only an explicitly-labelled *patient* address is captured
    paddr = _search(r"patient(?:'s)?\s*address\s*[:\-]\s*(.{5,120})$", text)
    if paddr:
        meta["patient_address"] = MetadataField(value=paddr, confidence=0.7)

    rno = _search(r"(?:report\s*(?:no|id|number)|lab\s*(?:no|id)|sample\s*(?:no|id)|accession\s*(?:no|number)|reg(?:istration)?\.?\s*no|visit\s*no|barcode)\.?\s*[:\-#]?\s*([A-Z0-9][A-Z0-9\-/]{2,30})", text)
    if rno:
        meta["report_number"] = MetadataField(value=rno, confidence=0.85)

    rdate = _date_after(r"(?:report(?:ed|ing)?|date\s*of\s*report|result)", text)
    cdate = _date_after(r"(?:collect(?:ed|ion)|sample\s*(?:collected|collection|drawn|received)?|specimen\s*collected)", text)
    if rdate:
        meta["report_date"] = MetadataField(value=rdate, confidence=0.9)
    if cdate:
        meta["collected_date"] = MetadataField(value=cdate, confidence=0.9)
    if not rdate:
        d = _date_after(r"\bdate", text) or (find_date(text).isoformat() if find_date(text) else None)
        if d:
            meta["report_date"] = MetadataField(value=d, confidence=0.6)

    if category_votes:
        top, n = category_votes.most_common(1)[0]
        total = sum(category_votes.values())
        meta["report_category"] = MetadataField(value=top, confidence=round(n / total, 3))
    return meta
