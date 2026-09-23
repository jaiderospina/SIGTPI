"""Document management endpoints."""
from uuid import UUID
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.document import DocumentRead, DocumentListResponse
from app.services.document_service import (
    upload_document, list_by_ti, get_document, get_file_path
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError

router = APIRouter()


@router.get("/ti/{ti_id}", response_model=DocumentListResponse, summary="Listar documentos de un TI")
async def list_documents(
    ti_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    docs = await list_by_ti(db, ti_id)
    return DocumentListResponse(total=len(docs), items=[DocumentRead.model_validate(d) for d in docs])


@router.post("/upload", response_model=DocumentRead, status_code=201, summary="Cargar documento con versionado")
async def upload(
    file: UploadFile = File(...),
    ti_id: UUID = Form(...),
    title: str = Form(""),
    doc_type: str = Form("advance"),
    description: str = Form(""),
    milestone_id: UUID | None = Form(None),
    current_user: TokenPayload = Depends(require_roles("EST","TUT","COO","ADM")),
    db: AsyncSession = Depends(get_db),
):
    if file.size and file.size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="El archivo supera el límite de 50 MB.")
    allowed = {"application/pdf","application/msword",
               "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
               "application/vnd.oasis.opendocument.text","text/plain"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=415, detail=f"Tipo de archivo no permitido: {file.content_type}")
    try:
        from uuid import UUID as U
        doc = await upload_document(
            db, ti_id=ti_id, uploaded_by=U(current_user.sub),
            file=file, title=title or file.filename or "Documento",
            doc_type=doc_type,
            description=description or None,
            milestone_id=milestone_id,
        )
        return DocumentRead.model_validate(doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{doc_id}", response_model=DocumentRead, summary="Obtener documento por ID")
async def get_doc(
    doc_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    return DocumentRead.model_validate(doc)


@router.get("/{doc_id}/download", summary="Descargar versión de un documento")
async def download(
    doc_id: UUID,
    version: int | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        file_path, filename = await get_file_path(db, doc_id, version)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    if not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en el servidor.")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


@router.get("/{doc_id}/similarity", summary="Ver reporte de similitud del documento")
async def similarity_report(
    doc_id: UUID,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","DIR","ADM","EST")),
    db: AsyncSession = Depends(get_db),
):
    doc = await get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado.")
    latest = doc.versions[-1] if doc.versions else None
    return {
        "document_id": str(doc_id),
        "title": doc.title,
        "version": latest.version_number if latest else None,
        "similarity_percent": latest.similarity_percent if latest else None,
        "status": "pending" if (latest and latest.similarity_percent is None) else "completed",
        "threshold": 20,
        "exceeds_threshold": (latest.similarity_percent or 0) > 20 if latest else False,
    }
