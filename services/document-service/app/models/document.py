import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Float, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = {"schema": "documents"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False, default="advance")
    current_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc))

    versions: Mapped[list["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="document",
        lazy="noload", cascade="all, delete-orphan",
        order_by="DocumentVersion.version_number")


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = {"schema": "documents"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.documents.id", ondelete="CASCADE"),
        nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    similarity_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_signed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document: Mapped["Document"] = relationship("Document", back_populates="versions")
