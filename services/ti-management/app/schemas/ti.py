from uuid import UUID
from datetime import datetime, date
from typing import Any
from pydantic import Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import TIStatus, MilestoneType, MilestoneStatus, KnowledgeArea


# ── Research Work ─────────────────────────────────────────────────────────────
class TICreateRequest(BaseSchema):
    assignment_id: UUID
    student_id: UUID
    tutor_id: UUID
    program_id: UUID
    title: str = Field(..., min_length=10, max_length=512)
    knowledge_area: KnowledgeArea
    problem_statement: str | None = None
    objectives: str | None = None
    methodology: str | None = None
    keywords: list[str] = []
    start_date: date | None = None
    estimated_defense: date | None = None


class TIUpdateRequest(BaseSchema):
    title: str | None = Field(None, min_length=10, max_length=512)
    problem_statement: str | None = None
    objectives: str | None = None
    methodology: str | None = None
    keywords: list[str] | None = None
    estimated_defense: date | None = None
    status: TIStatus | None = None


class AlertRead(BaseSchema):
    id: UUID
    level: str
    reason: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None


class AdvanceRead(BaseSchema):
    id: UUID
    period: str
    activities_done: str
    progress_percent: float
    obstacles: str | None
    action_plan: str | None
    registered_at: datetime


class MilestoneRead(BaseSchema):
    id: UUID
    name: str
    milestone_type: str
    status: str
    planned_date: date
    actual_date: date | None
    weight_percent: float
    is_critical: bool
    approved_at: datetime | None


class TIRead(IdentifiedSchema):
    assignment_id: UUID
    student_id: UUID
    tutor_id: UUID
    program_id: UUID
    title: str
    knowledge_area: str
    problem_statement: str | None
    objectives: str | None
    methodology: str | None
    keywords: list[str]
    status: str
    progress_percent: float
    start_date: date | None
    estimated_defense: date | None
    actual_defense: date | None
    milestones: list[MilestoneRead] = []
    advances: list[AdvanceRead] = []
    alerts: list[AlertRead] = []


class TISummary(BaseSchema):
    id: UUID
    student_id: UUID
    tutor_id: UUID
    title: str
    status: str
    progress_percent: float
    estimated_defense: date | None
    active_alerts: int = 0


# ── Milestone ─────────────────────────────────────────────────────────────────
class MilestoneCreateRequest(BaseSchema):
    ti_id: UUID
    name: str = Field(..., min_length=3, max_length=255)
    description: str | None = None
    milestone_type: MilestoneType
    planned_date: date
    weight_percent: float = Field(10.0, ge=0.1, le=100.0)
    is_critical: bool = False


class MilestoneApproveRequest(BaseSchema):
    approved: bool
    rejection_notes: str | None = None


# ── Progress ──────────────────────────────────────────────────────────────────
class AdvanceCreateRequest(BaseSchema):
    ti_id: UUID
    period: str = Field(..., pattern=r"^\d{4}-[12]$")
    activities_done: str = Field(..., min_length=10)
    progress_percent: float = Field(..., ge=0.0, le=100.0)
    obstacles: str | None = None
    action_plan: str | None = None


# ── Alert ─────────────────────────────────────────────────────────────────────
class AlertJustifyRequest(BaseSchema):
    justification: str = Field(..., min_length=10)


# ── KPI ───────────────────────────────────────────────────────────────────────
class TIStatusSummary(BaseSchema):
    total: int
    by_status: dict[str, int]
    at_risk: int
    overdue_milestones: int
    avg_progress: float
