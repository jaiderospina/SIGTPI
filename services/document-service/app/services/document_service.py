"""Document storage service — stores files locally with SHA-256 hashing."""
import hashlib, os, shutil
from uuid import UUID
from datetime import datetime, timezone
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.models.document import Document, DocumentVersion
from app.core.config import settings
from sigtpi_common.utils.logging import get_logger
from sigtpi_common.utils.exceptions import NotFoundError

logger = get_logger(__name__)


def _storage_path() -> Path:
    p = Path(settings.file_storage_path) / "documents"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _compute_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


async def upload_document(
    db: AsyncSession,
    ti_id: UUID,
    uploaded_by: UUID,
    file: UploadFile,
    title: str,
    doc_type: str,
    description: str | None = None,
    milestone_id: UUID | None = None,
) -> Document:
    content = await file.read()
    sha256 = _compute_hash(content)
    size = len(content)
    mime = file.content_type or "application/octet-stream"

    # Find or create document record for this ti+type+milestone
    result = await db.execute(
        select(Document)
        .options(selectinload(Document.versions))
        .where(Document.ti_id == ti_id, Document.doc_type == doc_type,
               Document.milestone_id == milestone_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        doc = Document(ti_id=ti_id, milestone_id=milestone_id, title=title,
                       description=description, doc_type=doc_type,
                       current_version=1, created_by=uploaded_by)
        db.add(doc)
        await db.flush()
        version_number = 1
    else:
        version_number = doc.current_version + 1
        doc.current_version = version_number
        doc.updated_at = datetime.now(timezone.utc)

    # Save file to disk
    file_dir = _storage_path() / str(doc.id)
    file_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"v{version_number}_{file.filename}"
    file_path = file_dir / safe_name
    file_path.write_bytes(content)

    version = DocumentVersion(
        document_id=doc.id, version_number=version_number,
        filename=file.filename or safe_name, file_path=str(file_path),
        file_size=size, mime_type=mime, sha256_hash=sha256,
        uploaded_by=uploaded_by,
    )
    db.add(version)
    await db.flush()
    logger.info("document_uploaded", doc_id=str(doc.id), version=version_number, hash=sha256[:16])
    return doc


async def list_by_ti(db: AsyncSession, ti_id: UUID) -> list[Document]:
    r = await db.execute(
        select(Document).options(selectinload(Document.versions))
        .where(Document.ti_id == ti_id).order_by(Document.created_at)
    )
    return list(r.scalars().all())


async def get_document(db: AsyncSession, doc_id: UUID) -> Document | None:
    r = await db.execute(
        select(Document).options(selectinload(Document.versions))
        .where(Document.id == doc_id)
    )
    return r.scalar_one_or_none()


async def get_file_path(db: AsyncSession, doc_id: UUID, version: int | None = None) -> tuple[str, str]:
    doc = await get_document(db, doc_id)
    if not doc:
        raise NotFoundError("Documento", doc_id)
    if version is not None:
        v = next((v for v in doc.versions if v.version_number == version), None)
    else:
        v = doc.versions[-1] if doc.versions else None
    if not v:
        raise NotFoundError("Versión", f"{doc_id}@v{version}")
    return v.file_path, v.filename
