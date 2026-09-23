from uuid import UUID
from datetime import datetime
from pydantic import Field
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import CertificateStatus, SignatureStatus


class CertificateIssueRequest(BaseSchema):
    user_id: UUID
    common_name: str = Field(..., min_length=2)
    email: str
    validity_days: int = Field(365, ge=30, le=1095)


class CertificateRead(IdentifiedSchema):
    user_id: UUID
    serial_number: str
    common_name: str
    email: str
    status: str
    issued_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class CertificateRevokeRequest(BaseSchema):
    reason: str = Field(..., min_length=5)


class SignDocumentRequest(BaseSchema):
    document_id: UUID
    document_type: str
    document_hash: str = Field(..., min_length=32, description="SHA-256 hex digest of the document")
    signer_id: UUID


class SignatureRead(IdentifiedSchema):
    document_id: UUID
    document_type: str
    signer_id: UUID
    certificate_id: UUID
    signature_hash: str
    document_hash: str
    signed_at: datetime
    is_valid: bool


class VerifySignatureRequest(BaseSchema):
    document_id: UUID
    document_hash: str


class VerifySignatureResponse(BaseSchema):
    document_id: UUID
    is_valid: bool
    signers: list[dict]
    verification_timestamp: datetime
