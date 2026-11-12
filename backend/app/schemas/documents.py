from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.constants import DocType, DocumentStatus


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UploadResponse(BaseModel):
    document_id: uuid.UUID
    status: DocumentStatus


class DocumentOut(ORM):
    id: uuid.UUID
    doc_type: DocType
    original_filename: str
    mime: str
    size_bytes: int
    pages: int
    status: DocumentStatus
    status_message: str | None = None
    lab_name: str | None = None
    lab_address: str | None = None
    patient_name: str | None = None
    doctor_name: str | None = None
    report_category: str | None = None
    report_date: date | None = None
    collected_date: date | None = None
    report_number: str | None = None
    uploaded_at: datetime
    description: str | None = None
    parameter_count: int = 0
    out_of_range_count: int = 0
    needs_verification_count: int = 0
    has_analysis: bool = False


class DocumentList(BaseModel):
    items: list[DocumentOut]
    total: int


class ParameterOut(ORM):
    id: uuid.UUID
    position: int
    parameter_id: str | None
    canonical_name: str | None = None
    name_raw: str
    value_num: float | None
    value_raw: str | None
    unit: str | None
    unit_normalized: str | None
    ref_low: float | None
    ref_high: float | None
    ref_raw: str | None
    lab_flag: str | None
    status: str
    finding_class: str | None
    confidence: float
    issues: list[str] = Field(default_factory=list)
    needs_verification: bool = False
    bbox_json: dict | None
    page_no: int
    verified: bool
    source_tag: str


class MetadataFieldOut(BaseModel):
    value: str | None = None
    confidence: float = 0.0


class ExtractionOut(BaseModel):
    document: DocumentOut
    metadata: dict[str, MetadataFieldOut] = Field(default_factory=dict)
    parameters: list[ParameterOut] = Field(default_factory=list)
    confidence_threshold: float
    warnings: list[str] = Field(default_factory=list)
    engine: str | None = None


# ---------- PATCH /documents/{id}/extraction (API-05) ----------
class MetadataPatch(BaseModel):
    lab_name: str | None = None
    lab_address: str | None = None
    patient_name: str | None = None
    patient_address: str | None = None
    doctor_name: str | None = None
    report_category: str | None = None
    report_date: date | None = None
    collected_date: date | None = None
    report_number: str | None = None
    description: str | None = None


class ParameterPatch(BaseModel):
    id: uuid.UUID
    name_raw: str | None = None
    parameter_id: str | None = None
    value_raw: str | None = None
    unit: str | None = None
    ref_raw: str | None = None
    lab_flag: str | None = None
    verified: bool | None = None
    delete: bool = False


class NewParameter(BaseModel):
    name_raw: str
    value_raw: str
    unit: str | None = None
    ref_raw: str | None = None
    parameter_id: str | None = None


class ExtractionPatch(BaseModel):
    metadata: MetadataPatch | None = None
    parameters: list[ParameterPatch] = Field(default_factory=list)
    new_parameters: list[NewParameter] = Field(default_factory=list)
    confirm: bool = False
    # Lab reports: let FITSCAN check flagged values itself. Values that pass every automated check are accepted;
    # the rest stay unverified and are left out of the AI analysis (BR-02) instead of blocking confirmation.
    auto_check: bool = False
