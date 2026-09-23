from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.pki import (
    CertificateIssueRequest, CertificateRead, CertificateRevokeRequest,
    SignDocumentRequest, SignatureRead, VerifySignatureRequest, VerifySignatureResponse,
)
from app.services.pki_service import (
    issue_certificate, revoke_certificate, sign_document, verify_signatures,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.post("/certificates", response_model=CertificateRead, status_code=201,
             summary="Emitir certificado X.509 para usuario")
async def issue_cert(
    data: CertificateIssueRequest,
    current_user: TokenPayload = Depends(require_roles("ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        cert = await issue_certificate(db, data)
        return CertificateRead.model_validate(cert)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/certificates/{cert_id}/revoke", response_model=CertificateRead,
             summary="Revocar certificado")
async def revoke_cert(
    cert_id: UUID, data: CertificateRevokeRequest,
    current_user: TokenPayload = Depends(require_roles("ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        cert = await revoke_certificate(db, cert_id, data, UUID(current_user.sub))
        return CertificateRead.model_validate(cert)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)


@router.post("/sign", response_model=SignatureRead, status_code=201,
             summary="Firmar documento digitalmente")
async def sign_doc(
    data: SignDocumentRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sig = await sign_document(db, data)
        return SignatureRead.model_validate(sig)
    except (ForbiddenError, ConflictError) as e:
        raise HTTPException(status_code=403 if isinstance(e, ForbiddenError) else 409, detail=e.message)


@router.post("/verify", response_model=VerifySignatureResponse, summary="Verificar firmas de documento")
async def verify(
    data: VerifySignatureRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await verify_signatures(db, data.document_id, data.document_hash)
    return VerifySignatureResponse(**result)
