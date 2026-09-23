from uuid import UUID
from datetime import datetime, date
from sigtpi_common.schemas.base import BaseSchema


class TIStatusKPI(BaseSchema):
    total_tis: int = 0
    total: int = 0
    active: int = 0
    in_progress: int = 0
    approved: int = 0
    withdrawn: int = 0
    at_risk: int = 0
    avg_progress: float = 0.0
    avg_months_to_defense: float | None = None


class TutorWorkloadKPI(BaseSchema):
    tutor_id: UUID
    active_students: int = 0
    active_tis: int = 0
    sessions_this_month: int = 0
    pending_reviews: int = 0
    avg_response_days: float = 0.0


class ProgramKPI(BaseSchema):
    program_id: UUID
    program_name: str
    graduation_rate: float = 0.0
    avg_duration_months: float = 0.0
    active_students: int = 0
    at_risk_students: int = 0
    tutor_count: int = 0


class StudentProgressReport(BaseSchema):
    student_id: UUID
    program_id: UUID
    ti_id: UUID | None = None
    ti_title: str | None = None
    status: str = "active"
    progress_percent: float = 0.0
    sessions_completed: int = 0
    milestones_approved: int = 0
    milestones_total: int = 0
    active_alerts: int = 0
    next_milestone: str | None = None
    next_milestone_date: date | None = None


class DashboardSummary(BaseSchema):
    generated_at: datetime
    total_students: int = 0
    total_tutors: int = 0
    total_tis: int = 0
    active_tis: int = 0
    tis_at_risk: int = 0
    at_risk_tis: int = 0
    sessions_this_week: int = 0
    pending_evaluations: int = 0
    unread_alerts: int = 0
    active_alerts: int = 0
    graduation_rate: float | None = None
    avg_graduation_months: float | None = None
    dropout_rate: float | None = None
    avg_sessions_per_ti: float | None = None
    level3_alerts: int = 0
    tutor_workload: list[dict] = []
    recent_activity: list[dict] = []
