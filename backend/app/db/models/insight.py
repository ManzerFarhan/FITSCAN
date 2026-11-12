import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, LargeBinary, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models._common import created_at_col, uuid_pk


class Analysis(Base):  # DB-09
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    summary_json: Mapped[dict] = mapped_column(JSON)
    observations_json: Mapped[list] = mapped_column(JSON)
    model: Mapped[str] = mapped_column(String(100))
    prompt_version: Mapped[str] = mapped_column(String(32))
    sources_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = created_at_col()


class ChatMessage(Base):  # DB-10
    __tablename__ = "chat_messages"

    id: Mapped[uuid.UUID] = uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = created_at_col()


class Comparison(Base):  # DB-11
    __tablename__ = "comparisons"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    guest_session_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True
    )
    document_ids: Mapped[list] = mapped_column(JSON)
    result_json: Mapped[dict] = mapped_column(JSON)
    summary_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at_col()


class CentreSearch(Base):  # DB-12
    __tablename__ = "centre_searches"

    id: Mapped[uuid.UUID] = uuid_pk()
    city: Mapped[str | None] = mapped_column(String(120))
    locality: Mapped[str | None] = mapped_column(String(120))
    query_json: Mapped[dict] = mapped_column(JSON)
    results_json: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = created_at_col()


class KBChunk(Base):  # DB-13
    __tablename__ = "kb_chunks"

    id: Mapped[uuid.UUID] = uuid_pk()
    source: Mapped[str] = mapped_column(String(64))
    url: Mapped[str] = mapped_column(String(1000))
    title: Mapped[str] = mapped_column(String(500))
    text: Mapped[str] = mapped_column(Text)
    embedding_ref: Mapped[int | None] = mapped_column()


class StoredFile(Base):  # uploaded files when STORAGE_BACKEND=db (free hosting without object storage)
    __tablename__ = "stored_files"

    key: Mapped[str] = mapped_column(String(512), primary_key=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    data: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[datetime] = created_at_col()
