import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sigtpi_common.utils.database import Base
from app.models.enums import CertificateStatus


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = {"schema": "pki"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    serial_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    common_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    public_key_pem: Mapped[str] = mapped_column(Text, nullable=False)
    certificate_pem: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=CertificateStatus.ACTIVE, nullable=False
    )
    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)


class DocumentSignature(Base):
    __tablename__ = "document_signatures"
    __table_args__ = {"schema": "pki"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    document_type: Mapped[str] = mapped_column(String(50), nullable=False)
    signer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    certificate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    signature_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    document_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    signed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
