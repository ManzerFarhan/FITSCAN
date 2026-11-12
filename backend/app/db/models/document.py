import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import DocumentStatus
from app.db.base import Base
from app.db.models._common import created_at_col, utcnow, uuid_pk


class Document(Base):  # DB-03
    __tablename__ = "documents"
    __table_args__ = (Index("ix_documents_user_report_date", "user_id", "report_date"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE")
    )
    guest_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True
    )
    doc_type: Mapped[str] = mapped_column(String(32))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))
    mime: Mapped[str] = mapped_column(String(64))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    pages: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.UPLOADED)
    status_message: Mapped[str | None] = mapped_column(String(500))
    lab_name: Mapped[str | None] = mapped_column(String(255))
    lab_address: Mapped[str | None] = mapped_column(String(500))
    patient_name: Mapped[str | None] = mapped_column(String(200))
    patient_address: Mapped[str | None] = mapped_column(String(500))
    doctor_name: Mapped[str | None] = mapped_column(String(200))
    report_category: Mapped[str | None] = mapped_column(String(32))
    report_date: Mapped[date | None] = mapped_column(Date)  # BR-14: actual date on document
    collected_date: Mapped[date | None] = mapped_column(Date)
    report_number: Mapped[str | None] = mapped_column(String(100))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)  # BR-14
    description: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)  # per-field confidence for metadata

    parameters: Mapped[list["Parameter"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", passive_deletes=True,
        order_by="Parameter.position",
    )


class ExtractionRun(Base):  # DB-04
    __tablename__ = "extraction_runs"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    engine: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(32))
    started_at: Mapped[datetime] = created_at_col()
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_json: Mapped[dict | None] = mapped_column(JSON)


class Parameter(Base):  # DB-05
    __tablename__ = "parameters"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    parameter_id: Mapped[str | None] = mapped_column(String(64), index=True)  # canonical
    name_raw: Mapped[str] = mapped_column(String(255))
    value_num: Mapped[float | None] = mapped_column(Float)
    value_raw: Mapped[str | None] = mapped_column(String(100))
    unit: Mapped[str | None] = mapped_column(String(50))
    unit_normalized: Mapped[str | None] = mapped_column(String(50))
    ref_low: Mapped[float | None] = mapped_column(Float)
    ref_high: Mapped[float | None] = mapped_column(Float)
    ref_raw: Mapped[str | None] = mapped_column(String(200))
    lab_flag: Mapped[str | None] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16))
    finding_class: Mapped[str | None] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    issues: Mapped[list | None] = mapped_column(JSON)  # sanity-check messages
    bbox_json: Mapped[dict | None] = mapped_column(JSON)
    page_no: Mapped[int] = mapped_column(Integer, default=1)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    source_tag: Mapped[str] = mapped_column(String(16))

    document: Mapped[Document] = relationship(back_populates="parameters")


class ParameterDictionary(Base):  # DB-06
    __tablename__ = "parameter_dictionary"

    parameter_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(32))
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    default_unit: Mapped[str | None] = mapped_column(String(50))
    plausible_min: Mapped[float | None] = mapped_column(Float)
    plausible_max: Mapped[float | None] = mapped_column(Float)
