from uuid import UUID
from datetime import datetime
from pydantic import Field
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import AssignmentStatus, CommitteeRole, CommitteeStatus


class AssignmentRequestCreate(BaseSchema):
    student_id: UUID
    tutor_id: UUID
    program_id: UUID
    research_area: str = Field(..., min_length=5, max_length=255)
    preliminary_title: str | None = Field(None, max_length=512)
    notes: str | None = None


class AssignmentResponseRequest(BaseSchema):
    accept: bool
    rejection_reason: str | None = Field(None, max_length=500)


class CoTutorAddRequest(BaseSchema):
    assignment_id: UUID
    tutor_id: UUID
    area_of_contribution: str | None = None


class CoTutorRead(BaseSchema):
    id: UUID
    tutor_id: UUID
    area_of_contribution: str | None
    added_at: datetime


class AssignmentRead(IdentifiedSchema):
    student_id: UUID
    tutor_id: UUID
    program_id: UUID
    research_area: str
    preliminary_title: str | None
    status: str
    rejection_reason: str | None
    assigned_by: UUID
    requested_at: datetime
    responded_at: datetime | None
    activated_at: datetime | None
    co_tutors: list[CoTutorRead] = []


class AssignmentSummary(BaseSchema):
    id: UUID
    student_id: UUID
    tutor_id: UUID
    program_id: UUID
    status: str
    research_area: str


class CommitteeMemberAdd(BaseSchema):
    evaluator_id: UUID
    role: CommitteeRole = CommitteeRole.MEMBER
    is_external: bool = False


class CommitteeMemberRead(BaseSchema):
    id: UUID
    evaluator_id: UUID
    role: str
    is_external: bool
    added_at: datetime


class CommitteeRead(IdentifiedSchema):
    assignment_id: UUID
    status: str
    formed_by: UUID
    formed_at: datetime
    notes: str | None
    members: list[CommitteeMemberRead] = []


class TutorWorkloadResponse(BaseSchema):
    tutor_id: UUID
    active_assignments: int
    pending_assignments: int
    max_students: int
    is_overloaded: bool
