from uuid import UUID
from datetime import datetime
from typing import Any
from pydantic import Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import SessionModality, SessionStatus, MinutesStatus


class CommitmentItem(BaseSchema):
    description: str
    deadline: str | None = None
    responsible: str | None = None


class SessionCreateRequest(BaseSchema):
    ti_id: UUID
    tutor_id: UUID
    student_id: UUID
    scheduled_at: datetime
    duration_minutes: int = Field(60, ge=15, le=480)
    modality: SessionModality
    agenda: str | None = None


class SessionUpdateRequest(BaseSchema):
    scheduled_at: datetime | None = None
    duration_minutes: int | None = Field(None, ge=15, le=480)
    modality: SessionModality | None = None
    agenda: str | None = None
    meeting_url: str | None = None


class SessionCancelRequest(BaseSchema):
    reason: str = Field(..., min_length=5)


class MinutesCreateRequest(BaseSchema):
    session_id: UUID
    topics_covered: str = Field(..., min_length=10)
    agreements: str | None = None
    commitments: list[CommitmentItem] = []
    tutor_observations: str | None = None


class MinutesStudentResponse(BaseSchema):
    confirm: bool
    student_observations: str | None = None
    dispute_reason: str | None = Field(None, description="Required if confirm=False")


class MinutesRead(BaseSchema):
    id: UUID
    session_id: UUID
    topics_covered: str
    agreements: str | None
    commitments: list[dict]
    tutor_observations: str | None
    student_observations: str | None
    status: str
    tutor_signed_at: datetime | None
    student_signed_at: datetime | None
    dispute_reason: str | None
    registered_at: datetime


class SessionRead(IdentifiedSchema):
    ti_id: UUID
    tutor_id: UUID
    student_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    modality: str
    status: str
    agenda: str | None
    meeting_url: str | None
    meeting_room_id: str | None
    cancellation_reason: str | None
    minutes: MinutesRead | None = None


class SessionSummary(BaseSchema):
    id: UUID
    ti_id: UUID
    scheduled_at: datetime
    modality: str
    status: str
    has_minutes: bool
    meeting_url: str | None


class VirtualRoomResponse(BaseSchema):
    room_id: str
    meeting_url: str
    provider: str = "jitsi"
