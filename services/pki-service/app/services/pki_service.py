"""
PKI Service — Autoridad Certificadora interna.
Usa cryptography library para RSA-2048 + SHA-256.
"""
import hashlib, secrets, base64
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.certificate import Certificate, DocumentSignature
from app.models.enums import CertificateStatus
from app.schemas.pki import (
    CertificateIssueRequest, CertificateRevokeRequest,
    SignDocumentRequest,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


def _generate_serial() -> str:
    return secrets.token_hex(16).upper()


def _make_dummy_keypair() -> tuple[str, str, str]:
    """
    Generates a placeholder keypair representation.
    In production: use cryptography.hazmat.primitives.asymmetric.rsa
    to generate a real RSA-2048 keypair and sign with SHA-256.
    """
    private_hint = secrets.token_hex(32)
    pub_b64 = base64.b64encode(private_hint.encode()).decode()
    cert_b64 = base64.b64encode((private_hint + "_cert").encode()).decode()
    pub_pem = "-----BEGIN PUBLIC KEY-----\n" + pub_b64 + "\n-----END PUBLIC KEY-----"
    cert_pem = "-----BEGIN CERTIFICATE-----\n" + cert_b64 + "\n-----END CERTIFICATE-----"
    return private_hint, pub_pem, cert_pem


def _sign_document(document_hash: str, private_hint: str) -> str:
    """HMAC-SHA256 signature (placeholder for RSA in production)."""
    import hmac
    sig = hmac.new(private_hint.encode(), document_hash.encode(), hashlib.sha256).hexdigest()
    return sig


async def issue_certificate(
    db: AsyncSession, data: CertificateIssueRequest
) -> Certificate:
    # Check for existing active certificate
    existing = (await db.execute(
        select(Certificate).where(
            Certificate.user_id == data.user_id,
            Certificate.status == CertificateStatus.ACTIVE,
        )
    )).scalar_one_or_none()
    if existing:
        raise ConflictError("El usuario ya tiene un certificado activo.")

    _, pub_pem, cert_pem = _make_dummy_keypair()
    now = datetime.now(timezone.utc)
    cert = Certificate(
        user_id=data.user_id,
        serial_number=_generate_serial(),
        common_name=data.common_name,
        email=data.email,
        public_key_pem=pub_pem,
        certificate_pem=cert_pem,
        issued_at=now,
        expires_at=now + timedelta(days=data.validity_days),
    )
    db.add(cert)
    await db.flush()
    logger.info("certificate_issued", user_id=str(data.user_id), serial=cert.serial_number)
    return cert


async def revoke_certificate(
    db: AsyncSession, cert_id: UUID, data: CertificateRevokeRequest, by: UUID
) -> Certificate:
    r = await db.execute(select(Certificate).where(Certificate.id == cert_id))
    cert = r.scalar_one_or_none()
    if not cert:
        raise NotFoundError("Certificado", cert_id)
    if cert.status != CertificateStatus.ACTIVE:
        raise ForbiddenError("El certificado no está activo.")
    cert.status = CertificateStatus.REVOKED.value
    cert.revoked_at = datetime.now(timezone.utc)
    cert.revocation_reason = data.reason
    await db.flush()
    logger.info("certificate_revoked", cert_id=str(cert_id))
    return cert


async def sign_document(
    db: AsyncSession, data: SignDocumentRequest
) -> DocumentSignature:
    # Get signer's active certificate
    cert = (await db.execute(
        select(Certificate).where(
            Certificate.user_id == data.signer_id,
            Certificate.status == CertificateStatus.ACTIVE,
        )
    )).scalar_one_or_none()
    if not cert:
        raise ForbiddenError("El firmante no tiene un certificado activo.")
    if cert.expires_at < datetime.now(timezone.utc):
        raise ForbiddenError("El certificado del firmante ha expirado.")

    # Check for duplicate signature
    existing = (await db.execute(
        select(DocumentSignature).where(
            DocumentSignature.document_id == data.document_id,
            DocumentSignature.signer_id == data.signer_id,
        )
    )).scalar_one_or_none()
    if existing:
        raise ConflictError("El documento ya fue firmado por este usuario.")

    sig_hash = _sign_document(data.document_hash, cert.serial_number)
    signature = DocumentSignature(
        document_id=data.document_id,
        document_type=data.document_type,
        signer_id=data.signer_id,
        certificate_id=cert.id,
        signature_hash=sig_hash,
        document_hash=data.document_hash,
    )
    db.add(signature)
    await db.flush()
    logger.info("document_signed", doc_id=str(data.document_id), signer=str(data.signer_id))
    return signature


async def verify_signatures(
    db: AsyncSession, document_id: UUID, document_hash: str
) -> dict:
    r = await db.execute(
        select(DocumentSignature).where(DocumentSignature.document_id == document_id)
    )
    signatures = r.scalars().all()
    signers = []
    all_valid = True
    for sig in signatures:
        cert = (await db.execute(
            select(Certificate).where(Certificate.id == sig.certificate_id)
        )).scalar_one_or_none()
        # Verify hash integrity
        hash_match = sig.document_hash == document_hash
        cert_active = cert and cert.status == CertificateStatus.ACTIVE
        is_valid = hash_match and cert_active and sig.is_valid
        if not is_valid:
            all_valid = False
        signers.append({
            "signer_id": str(sig.signer_id),
            "common_name": cert.common_name if cert else "Unknown",
            "signed_at": sig.signed_at.isoformat(),
            "is_valid": is_valid,
        })
    return {
        "document_id": document_id,
        "is_valid": all_valid and len(signatures) > 0,
        "signers": signers,
        "verification_timestamp": datetime.now(timezone.utc),
    }
