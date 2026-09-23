from uuid import UUID
from datetime import datetime
from pydantic import Field
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema


class DocumentVersionRead(BaseSchema):
    id: UUID
    version_number: int
    filename: str
    file_size: int
    mime_type: str
    sha256_hash: str
    similarity_percent: float | None
    is_signed: bool
    uploaded_by: UUID
    created_at: datetime


class DocumentRead(IdentifiedSchema):
    ti_id: UUID
    milestone_id: UUID | None
    title: str
    description: str | None
    doc_type: str
    current_version: int
    versions: list[DocumentVersionRead] = []


class DocumentListResponse(BaseSchema):
    total: int
    items: list[DocumentRead]
