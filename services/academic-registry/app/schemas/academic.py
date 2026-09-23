from uuid import UUID
from datetime import datetime, date
from pydantic import Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import ProgramLevel, ProgramStatus, StudentStatus, SemesterGradeStatus


# ── Program ───────────────────────────────────────────────────────────────────
class ProgramCreateRequest(BaseSchema):
    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=5, max_length=255)
    level: ProgramLevel = ProgramLevel.MAESTRIA
    duration_semesters: int | None = Field(None, ge=1, le=16)
    duration_months: int | None = Field(None, ge=6, le=120)
    max_students_per_tutor: int = Field(5, ge=1, le=20)
    min_gpa_for_ti: float = Field(3.5, ge=0.0, le=5.0)
    description: str | None = None
    director_id: UUID | None = None
    coordinator_email: str | None = None
    status: ProgramStatus = ProgramStatus.ACTIVE

    @property
    def effective_duration_semesters(self) -> int:
        if self.duration_semesters:
            return self.duration_semesters
        if self.duration_months:
            return max(1, self.duration_months // 6)
        return 4


class ProgramUpdateRequest(BaseSchema):
    name: str | None = Field(None, min_length=5, max_length=255)
    duration_semesters: int | None = Field(None, ge=1, le=16)
    duration_months: int | None = Field(None, ge=6, le=120)
    max_students_per_tutor: int | None = Field(None, ge=1, le=20)
    min_gpa_for_ti: float | None = Field(None, ge=0.0, le=5.0)
    description: str | None = None
    director_id: UUID | None = None
    coordinator_email: str | None = None
    status: ProgramStatus | None = None


class ProgramRead(IdentifiedSchema):
    code: str
    name: str
    level: str
    duration_semesters: int
    duration_months: int | None = None
    max_students_per_tutor: int
    min_gpa_for_ti: float
    description: str | None = None
    status: str
    director_id: UUID | None = None
    coordinator_email: str | None = None


class ProgramSummary(BaseSchema):
    id: UUID
    code: str
    name: str
    level: str
    status: str


# ── Enrollment ────────────────────────────────────────────────────────────────
class EnrollmentCreateRequest(BaseSchema):
    student_id: UUID
    program_id: UUID
    cohort: str = Field(..., pattern=r"^\d{4}-[12]$")
    enrollment_date: date
    expected_graduation: date | None = None


class EnrollmentUpdateRequest(BaseSchema):
    status: StudentStatus | None = None
    expected_graduation: date | None = None
    notes: str | None = None


class SemesterGradeRead(BaseSchema):
    id: UUID
    semester: str
    grade: float
    tutor_id: UUID
    status: str
    comments: str | None
    recorded_at: datetime


class EnrollmentRead(IdentifiedSchema):
    student_id: UUID
    program_id: UUID
    cohort: str
    status: str
    enrollment_date: date
    expected_graduation: date | None
    actual_graduation: date | None
    gpa: float
    ti_approved: bool
    notes: str | None
    grades: list[SemesterGradeRead] = []


class EnrollmentSummary(BaseSchema):
    id: UUID
    student_id: UUID
    program_id: UUID
    cohort: str
    status: str
    gpa: float
    ti_approved: bool


# ── Semester Grade ─────────────────────────────────────────────────────────────
class GradeSubmitRequest(BaseSchema):
    enrollment_id: UUID
    semester: str = Field(..., pattern=r"^\d{4}-[12]$")
    grade: float = Field(..., ge=0.0, le=5.0)
    comments: str | None = None


class GradeApproveRequest(BaseSchema):
    grade_id: UUID


# ── Prerequisite check ────────────────────────────────────────────────────────
class PrerequisiteCheckRequest(BaseSchema):
    student_id: UUID
    program_id: UUID
    check_type: str = Field(..., description="ti_start | defense_preliminary | defense_final")


class PrerequisiteCheckResponse(BaseSchema):
    student_id: UUID
    program_id: UUID
    check_type: str
    meets_requirements: bool
    details: dict
