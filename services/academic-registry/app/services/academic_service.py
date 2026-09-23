from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.program import Program
from app.models.enrollment import Enrollment, SemesterGrade
from app.models.enums import ProgramStatus, StudentStatus, SemesterGradeStatus
from app.schemas.academic import (
    ProgramCreateRequest, ProgramUpdateRequest,
    EnrollmentCreateRequest, EnrollmentUpdateRequest,
    GradeSubmitRequest,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


# ── Programs ───────────────────────────────────────────────────────────────────
async def get_program(db: AsyncSession, program_id: UUID) -> Program | None:
    r = await db.execute(select(Program).where(Program.id == program_id))
    return r.scalar_one_or_none()


async def get_program_by_code(db: AsyncSession, code: str) -> Program | None:
    r = await db.execute(select(Program).where(Program.code == code.upper()))
    return r.scalar_one_or_none()


async def list_programs(db: AsyncSession, status: str | None = None) -> list[Program]:
    q = select(Program)
    if status:
        q = q.where(Program.status == status)
    r = await db.execute(q.order_by(Program.name))
    return list(r.scalars().all())


async def create_program(db: AsyncSession, data: ProgramCreateRequest) -> Program:
    existing = await get_program_by_code(db, data.code)
    if existing:
        raise ConflictError(f"Ya existe un programa con código '{data.code}'.")
    # Build dict with only valid columns, converting Enums to string values
    dumped = data.model_dump()
    valid_cols = {c.name for c in Program.__table__.columns}
    program_data = {}
    for k, v in dumped.items():
        if k not in valid_cols or v is None:
            continue
        # Convert Python Enum to its string value for VARCHAR columns
        program_data[k] = v.value if hasattr(v, 'value') else v
    # duration_months → duration_semesters conversion
    if dumped.get("duration_months") and "duration_semesters" not in program_data:
        program_data["duration_semesters"] = max(1, dumped["duration_months"] // 6)
    program = Program(**program_data)
    program.code = program.code.upper()
    db.add(program)
    await db.flush()
    logger.info("program_created", code=program.code, name=program.name)
    return program


async def update_program(db: AsyncSession, program_id: UUID, data: ProgramUpdateRequest) -> Program:
    program = await get_program(db, program_id)
    if not program:
        raise NotFoundError("Programa", program_id)
    for field, value in data.model_dump(exclude_none=True).items():
        # Convert Enum to string value for VARCHAR columns
        setattr(program, field, value.value if hasattr(value, 'value') else value)
    program.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return program


# ── Enrollments ────────────────────────────────────────────────────────────────
async def get_enrollment(db: AsyncSession, enrollment_id: UUID) -> Enrollment | None:
    r = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.grades))
        .where(Enrollment.id == enrollment_id)
    )
    return r.scalar_one_or_none()


async def get_enrollment_by_student_program(
    db: AsyncSession, student_id: UUID, program_id: UUID
) -> Enrollment | None:
    r = await db.execute(
        select(Enrollment)
        .options(selectinload(Enrollment.grades))
        .where(Enrollment.student_id == student_id, Enrollment.program_id == program_id)
    )
    return r.scalar_one_or_none()


async def list_enrollments(
    db: AsyncSession,
    program_id: UUID | None = None,
    cohort: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[int, list[Enrollment]]:
    q = select(Enrollment).options(selectinload(Enrollment.grades))
    if program_id:
        q = q.where(Enrollment.program_id == program_id)
    if cohort:
        q = q.where(Enrollment.cohort == cohort)
    if status:
        q = q.where(Enrollment.status == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
    return total, list(items)


async def create_enrollment(db: AsyncSession, data: EnrollmentCreateRequest) -> Enrollment:
    program = await get_program(db, data.program_id)
    if not program:
        raise NotFoundError("Programa", data.program_id)
    if program.status != ProgramStatus.ACTIVE:
        raise ForbiddenError("El programa no está activo.")
    existing = await get_enrollment_by_student_program(db, data.student_id, data.program_id)
    if existing:
        raise ConflictError("El estudiante ya está matriculado en este programa.")
    enrollment = Enrollment(**data.model_dump())
    db.add(enrollment)
    await db.flush()
    logger.info("enrollment_created", student=str(data.student_id), program=str(data.program_id))
    return enrollment


async def update_enrollment_status(
    db: AsyncSession, enrollment_id: UUID, data: EnrollmentUpdateRequest
) -> Enrollment:
    enrollment = await get_enrollment(db, enrollment_id)
    if not enrollment:
        raise NotFoundError("Matrícula", enrollment_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(enrollment, field, value)
    enrollment.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return enrollment


# ── Grades ────────────────────────────────────────────────────────────────────
async def submit_grade(
    db: AsyncSession, data: GradeSubmitRequest, tutor_id: UUID
) -> SemesterGrade:
    enrollment = await get_enrollment(db, data.enrollment_id)
    if not enrollment:
        raise NotFoundError("Matrícula", data.enrollment_id)
    if enrollment.status != StudentStatus.ACTIVE:
        raise ForbiddenError("Solo se pueden registrar notas para estudiantes activos.")
    # Check for duplicate
    existing = next((g for g in enrollment.grades if g.semester == data.semester), None)
    if existing:
        raise ConflictError(f"Ya existe una nota para el semestre {data.semester}.")
    grade = SemesterGrade(
        enrollment_id=data.enrollment_id,
        semester=data.semester,
        grade=data.grade,
        tutor_id=tutor_id,
        comments=data.comments,
    )
    db.add(grade)
    # Recalculate GPA
    all_grades = [g.grade for g in enrollment.grades] + [data.grade]
    approved = [g for g in all_grades if g >= 3.0]
    enrollment.gpa = round(sum(approved) / len(approved), 2) if approved else 0.0
    await db.flush()
    logger.info("grade_submitted", enrollment=str(data.enrollment_id), semester=data.semester, grade=data.grade)
    return grade


async def approve_grade(db: AsyncSession, grade_id: UUID, approved_by: UUID) -> SemesterGrade:
    r = await db.execute(select(SemesterGrade).where(SemesterGrade.id == grade_id))
    grade = r.scalar_one_or_none()
    if not grade:
        raise NotFoundError("Calificación", grade_id)
    if grade.status != SemesterGradeStatus.SUBMITTED:
        raise ForbiddenError("Solo se pueden aprobar calificaciones en estado 'submitted'.")
    grade.status = SemesterGradeStatus.APPROVED.value
    await db.flush()
    return grade


# ── Prerequisite check ─────────────────────────────────────────────────────────
async def check_prerequisites(
    db: AsyncSession, student_id: UUID, program_id: UUID, check_type: str
) -> dict:
    enrollment = await get_enrollment_by_student_program(db, student_id, program_id)
    if not enrollment:
        return {"meets_requirements": False, "details": {"error": "No enrollment found"}}
    program = await get_program(db, program_id)

    if check_type == "ti_start":
        meets = (
            enrollment.status == StudentStatus.ACTIVE
            and enrollment.gpa >= (program.min_gpa_for_ti if program else 3.5)
        )
        return {
            "meets_requirements": meets,
            "details": {
                "status": enrollment.status,
                "gpa": enrollment.gpa,
                "required_gpa": program.min_gpa_for_ti if program else 3.5,
            }
        }
    elif check_type == "defense_preliminary":
        approved_grades = [g for g in enrollment.grades if g.status == SemesterGradeStatus.APPROVED]
        meets = len(approved_grades) >= 2 and enrollment.gpa >= 3.5
        return {
            "meets_requirements": meets,
            "details": {"approved_semesters": len(approved_grades), "gpa": enrollment.gpa}
        }
    elif check_type == "defense_final":
        meets = enrollment.ti_approved and enrollment.gpa >= 3.5
        return {
            "meets_requirements": meets,
            "details": {"ti_approved": enrollment.ti_approved, "gpa": enrollment.gpa}
        }
    return {"meets_requirements": False, "details": {"error": f"Unknown check_type: {check_type}"}}
