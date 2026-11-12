"""Lab report pipeline orchestrator (P2-14). bytes -> LabExtractionResult. Pure (no DB)."""
from __future__ import annotations

import re
from collections import Counter

from pydantic import BaseModel, Field

from app.core.constants import DocumentStatus, ParameterStatus
from app.pipelines.base import BBox, LoadedDocument, MetadataField, StageCallback
from app.pipelines.lab_report.confidence import combine_confidence, needs_verification, sanity_issues
from app.pipelines.lab_report.metadata_extractor import extract_metadata
from app.pipelines.lab_report.normalizer import match_parameter
from app.pipelines.lab_report.range_parser import parse_range
from app.pipelines.lab_report.status_calculator import compute_status, normalize_lab_flag
from app.pipelines.lab_report.table_parser import parse_tables
from app.pipelines.layout import group_lines
from app.pipelines.ocr.printed_ocr import get_printed_ocr
from app.pipelines.preprocessing.image_enhance import enhance
from app.pipelines.preprocessing.pdf_loader import load_document
from app.utils.units import normalize_unit

VERSION = "lab-0.2.0"


class ExtractedParameter(BaseModel):
    position: int
    parameter_id: str | None
    canonical_name: str | None
    category: str | None
    name_raw: str
    value_num: float | None
    value_raw: str | None
    unit: str | None
    unit_normalized: str | None
    ref_low: float | None
    ref_high: float | None
    ref_raw: str | None
    lab_flag: str | None
    status: ParameterStatus
    confidence: float
    issues: list[str] = Field(default_factory=list)
    needs_verification: bool
    bbox: BBox | None
    page_no: int


class LabExtractionResult(BaseModel):
    engine: str
    version: str = VERSION
    is_digital: bool
    pages: int
    metadata: dict[str, MetadataField]
    parameters: list[ExtractedParameter]
    warnings: list[str] = Field(default_factory=list)
    lines: list[str] = Field(default_factory=list)  # raw text (stored in extraction_runs only)

    @property
    def needs_verification(self) -> bool:
        return any(p.needs_verification for p in self.parameters) or not self.parameters


# Report headers/footers that a table parser can mistake for a "test - value" row. Matched on the row's name.
_BOILERPLATE = re.compile(
    r"\b(?:tests?\s+performed\s+at|performed\s+at|booking\s+cent(?:re|er)|collection\s+cent(?:re|er)|authenticity|"
    r"verif(?:y|ied)\s+by\s+scanning|q\.?r\.?\s*code|page\s+\d+\s+of\s+\d+|end\s+of\s+(?:the\s+)?report|"
    r"conditions?\s+of\s+reporting|helpline|toll\s*free|registered\s+office|regd\.?\s+office|corporate\s+office|"
    r"printed\s+on|report(?:ing)?\s+(?:date|status)|collection\s+date|sample\s+(?:collected|received)|"
    r"patient\s+name|referr?(?:ed|ing)\s+(?:by|doctor)|ref\.?\s+doctor|lab\s*id|uhid|"
    r"pathologist|consultant|authori[sz]ed\s+signatory|electronically\s+signed)\b"
    r"|www\.|https?://|\S+@\S+\.\w+|\bcin\s*[:\-]|\bphone\s*[:\-]|\btel\s*[:\-]",
    re.IGNORECASE,
)
# Notes, comments, interpretation paragraphs etc. - not test rows, even if they contain numbers.
_NOTE_PREFIX = re.compile(
    r"^\s*(?:[*#•]|(?:[\-]+\s*)?(?:notes?|comments?|remarks?|interpretations?|clinical\s+(?:significance|notes?|info\w*)|"
    r"impression|advice|suggest\w*|disclaimer|methodology|method|specimen|sample\s+type|kit|instrument|reagent|"
    r"references?|please|kindly|this\s+(?:test|report|assay)|the\s+(?:test|report|results?)|results?\s+(?:are|should|may)|"
    r"tests?\s+(?:performed|done|carried)|(?:in|for)\s+(?:case|patients|adults|children)|decision\s+limits?|"
    r"risk\s+categor\w*|as\s+per)(?:\b|(?<=[:\-])))",
    re.IGNORECASE,
)
# Sentence-like names with no dictionary match are paragraph text, not test names.
_SENTENCE_WORDS = 8


def is_boilerplate(name: str) -> bool:
    return bool(_BOILERPLATE.search(name or ""))


def is_note_or_paragraph(name: str, matched: bool) -> bool:
    """True for note/comment/interpretation lines and long paragraph text - FITSCAN reads test rows only."""
    n = (name or "").strip()
    if _NOTE_PREFIX.match(n):
        return True
    return not matched and (len(n.split()) >= _SENTENCE_WORDS or len(n) > 60)


def parse_number(raw: str | None) -> float | None:
    if raw is None:
        return None
    s = raw.strip().lstrip("<>").strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def build_parameter(position: int, name_raw: str, value_raw: str | None, unit_raw: str | None,
                    ref_raw: str | None, flag_raw: str | None, ocr_conf: float, bbox: BBox | None,
                    page_no: int, threshold: float, sex: str | None = None, ambiguous: bool = False,
                    parameter_id: str | None = None) -> ExtractedParameter:
    """Shared by the pipeline and by user corrections, so both compute status identically."""
    if parameter_id:
        from app.utils import dictionaries

        p = dictionaries.parameters().get(parameter_id)
        match_pid, match_name, match_cat, name_score = parameter_id, p and p["canonical_name"], p and p["category"], 1.0
    else:
        m = match_parameter(name_raw)
        match_pid, match_name, match_cat, name_score = m.parameter_id, m.canonical_name, m.category, m.score
    value_num = parse_number(value_raw)
    ref = parse_range(ref_raw, sex=sex)
    issues = sanity_issues(match_pid, value_num, value_raw, unit_raw, ref)
    if ambiguous:
        issues.append("AMBIGUOUS_ASSOCIATION")
    if ref.kind == "sex_specific":
        issues.append("SEX_SPECIFIC_RANGE")
    if not match_pid and (len(name_raw.split()) >= _SENTENCE_WORDS or len(name_raw) > 55 or is_boilerplate(name_raw)):
        issues.append("LIKELY_NOT_A_TEST")
    conf = combine_confidence(ocr_conf, name_score, issues)
    return ExtractedParameter(
        position=position, parameter_id=match_pid, canonical_name=match_name, category=match_cat,
        name_raw=name_raw, value_num=value_num, value_raw=value_raw, unit=unit_raw,
        unit_normalized=normalize_unit(unit_raw), ref_low=ref.low, ref_high=ref.high, ref_raw=ref_raw,
        lab_flag=normalize_lab_flag(flag_raw), status=compute_status(value_num, ref), confidence=conf,
        issues=issues, needs_verification=needs_verification(conf, issues, threshold), bbox=bbox, page_no=page_no,
    )


class LabReportPipeline:
    def __init__(self, threshold: float = 0.85, max_pages: int = 30, on_stage: StageCallback | None = None):
        self.threshold = threshold
        self.max_pages = max_pages
        self.on_stage = on_stage or (lambda _s: None)

    def _ocr(self, doc: LoadedDocument) -> str:
        ocr_pages = [p for p in doc.pages if p.source == "ocr"]
        if not ocr_pages:
            return "native-text"
        self.on_stage(DocumentStatus.OCR_RUNNING)
        ocr = get_printed_ocr()

        def read(page) -> None:
            page.words = ocr.run(enhance(page.image), page.page_no)

        workers = min(len(ocr_pages), ocr.parallel_pages)
        if workers > 1:  # scanned multi-page reports: pages are read at the same time
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(workers, thread_name_prefix="ocr") as pool:
                list(pool.map(read, ocr_pages))
        else:
            for page in ocr_pages:
                read(page)
        return f"native-text+{ocr.engine_name}" if doc.is_digital is False and len(ocr_pages) < len(doc.pages) else ocr.engine_name

    def run(self, data: bytes, mime: str, sex: str | None = None) -> LabExtractionResult:
        self.on_stage(DocumentStatus.PREPROCESSING)
        doc = load_document(data, mime, self.max_pages)
        engine = self._ocr(doc)

        self.on_stage(DocumentStatus.EXTRACTING)
        words = [w for p in doc.pages for w in p.words]
        lines = group_lines(words)

        # Sex (for sex-specific ranges) only from the document itself or caller - never guessed.
        pre_meta = extract_metadata(lines)
        if not sex and "patient_sex" in pre_meta:
            sex = pre_meta["patient_sex"].value

        params: list[ExtractedParameter] = []
        skipped = 0
        for row in parse_tables(lines):
            # Only test rows: skip header/footer text ("Booking Centre :5498 - ...") and notes / long paragraphs.
            matched = match_parameter(row.name_raw).parameter_id is not None
            full = row.line_text or row.name_raw
            if (is_boilerplate(row.name_raw) or is_note_or_paragraph(row.name_raw, matched)
                    or (not matched and (is_boilerplate(full) or is_note_or_paragraph(full, matched)))):
                skipped += 1
                continue
            params.append(build_parameter(
                len(params), row.name_raw, row.value_raw, row.unit_raw, row.ref_raw, row.flag_raw,
                row.conf, row.bbox, row.page_no, self.threshold, sex=sex, ambiguous=row.ambiguous,
            ))

        votes = Counter(p.category for p in params if p.category)
        metadata = extract_metadata(lines, votes)
        warnings = []
        if not params:
            warnings.append("NO_PARAMETERS_FOUND")
        if skipped:
            warnings.append("BOILERPLATE_ROWS_SKIPPED")
        if not words:
            warnings.append("NO_TEXT_FOUND")
        return LabExtractionResult(
            engine=engine, is_digital=doc.is_digital, pages=len(doc.pages), metadata=metadata,
            parameters=params, warnings=warnings, lines=[re.sub(r"\s+", " ", ln.text) for ln in lines],
        )
