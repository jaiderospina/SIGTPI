from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models.assignment import TutorAssignment, CoTutor
from app.models.committee import EvaluationCommittee, CommitteeMember
from app.models.enums import AssignmentStatus, CommitteeStatus
from app.schemas.tutoring import (
    AssignmentRequestCreate, AssignmentResponseRequest,
    CoTutorAddRequest, CommitteeMemberAdd,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)
DEFAULT_MAX_STUDENTS = 5


async def _get_assignment(db: AsyncSession, assignment_id: UUID) -> TutorAssignment | None:
    r = await db.execute(
        select(TutorAssignment)
        .options(selectinload(TutorAssignment.co_tutors))
        .where(TutorAssignment.id == assignment_id)
    )
    return r.scalar_one_or_none()


async def get_tutor_workload(db: AsyncSession, tutor_id: UUID, max_students: int = DEFAULT_MAX_STUDENTS) -> dict:
    active = (await db.execute(
        select(func.count()).where(
            TutorAssignment.tutor_id == tutor_id,
            TutorAssignment.status == AssignmentStatus.ACTIVE,
        )
    )).scalar_one()
    pending = (await db.execute(
        select(func.count()).where(
            TutorAssignment.tutor_id == tutor_id,
            TutorAssignment.status == AssignmentStatus.PENDING,
        )
    )).scalar_one()
    return {
        "tutor_id": tutor_id, "active_assignments": active,
        "pending_assignments": pending, "max_students": max_students,
        "is_overloaded": active >= max_students,
    }


async def create_assignment(
    db: AsyncSession, data: AssignmentRequestCreate, assigned_by: UUID
) -> TutorAssignment:
    # Prevent duplicate active assignments for same student+program
    existing = (await db.execute(
        select(TutorAssignment).where(
            TutorAssignment.student_id == data.student_id,
            TutorAssignment.program_id == data.program_id,
            TutorAssignment.status.in_([AssignmentStatus.PENDING, AssignmentStatus.ACTIVE]),
        )
    )).scalar_one_or_none()
    if existing:
        raise ConflictError("El estudiante ya tiene una tutoría activa o pendiente en este programa.")

    # Conflict of interest: tutor cannot supervise and evaluate the same TI
    assignment = TutorAssignment(
        student_id=data.student_id,
        tutor_id=data.tutor_id,
        program_id=data.program_id,
        research_area=data.research_area,
        preliminary_title=data.preliminary_title,
        notes=data.notes,
        assigned_by=assigned_by,
    )
    db.add(assignment)
    await db.flush()
    logger.info("assignment_created", student=str(data.student_id), tutor=str(data.tutor_id))
    return assignment


async def respond_to_assignment(
    db: AsyncSession, assignment_id: UUID, tutor_id: UUID, data: AssignmentResponseRequest
) -> TutorAssignment:
    assignment = await _get_assignment(db, assignment_id)
    if not assignment:
        raise NotFoundError("Asignación", assignment_id)
    if assignment.tutor_id != tutor_id:
        raise ForbiddenError("Solo el tutor asignado puede responder.")
    if assignment.status != AssignmentStatus.PENDING:
        raise ForbiddenError("Solo se puede responder a asignaciones pendientes.")

    now = datetime.now(timezone.utc)
    assignment.responded_at = now
    if data.accept:
        assignment.status = AssignmentStatus.ACCEPTED.value
        assignment.activated_at = now
    else:
        if not data.rejection_reason:
            raise ForbiddenError("Debe indicar el motivo de rechazo.")
        assignment.status = AssignmentStatus.REJECTED.value
        assignment.rejection_reason = data.rejection_reason
    await db.flush()
    logger.info("assignment_responded", id=str(assignment_id), accepted=data.accept)
    return assignment


async def add_co_tutor(db: AsyncSession, data: CoTutorAddRequest, added_by: UUID) -> CoTutor:
    assignment = await _get_assignment(db, data.assignment_id)
    if not assignment:
        raise NotFoundError("Asignación", data.assignment_id)
    if assignment.status not in [AssignmentStatus.ACCEPTED, AssignmentStatus.ACTIVE]:
        raise ForbiddenError("Solo se pueden añadir co-tutores a asignaciones activas o aceptadas.")
    # Prevent conflict of interest
    if data.tutor_id == assignment.tutor_id:
        raise ConflictError("El tutor principal no puede ser co-tutor del mismo TI.")
    existing = next((c for c in assignment.co_tutors if c.tutor_id == data.tutor_id), None)
    if existing:
        raise ConflictError("Este docente ya es co-tutor de esta asignación.")
    co_tutor = CoTutor(
        assignment_id=data.assignment_id,
        tutor_id=data.tutor_id,
        area_of_contribution=data.area_of_contribution,
    )
    db.add(co_tutor)
    await db.flush()
    return co_tutor


async def list_assignments(
    db: AsyncSession,
    tutor_id: UUID | None = None,
    student_id: UUID | None = None,
    status: str | None = None,
    program_id: UUID | None = None,
    page: int = 1, page_size: int = 20,
) -> tuple[int, list[TutorAssignment]]:
    q = select(TutorAssignment).options(selectinload(TutorAssignment.co_tutors))
    if tutor_id:
        q = q.where(TutorAssignment.tutor_id == tutor_id)
    if student_id:
        q = q.where(TutorAssignment.student_id == student_id)
    if status:
        q = q.where(TutorAssignment.status == status)
    if program_id:
        q = q.where(TutorAssignment.program_id == program_id)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
    return total, list(items)


# ── Committee ─────────────────────────────────────────────────────────────────
async def create_committee(
    db: AsyncSession, assignment_id: UUID, members: list[CommitteeMemberAdd], formed_by: UUID
) -> EvaluationCommittee:
    assignment = await _get_assignment(db, assignment_id)
    if not assignment:
        raise NotFoundError("Asignación", assignment_id)
    existing_committee = (await db.execute(
        select(EvaluationCommittee).where(EvaluationCommittee.assignment_id == assignment_id)
    )).scalar_one_or_none()
    if existing_committee:
        raise ConflictError("Ya existe un comité para esta asignación.")
    # Conflict of interest: tutor principal cannot be committee member
    member_ids = {m.evaluator_id for m in members}
    if assignment.tutor_id in member_ids:
        raise ConflictError("El tutor principal no puede ser miembro del comité evaluador.")

    committee = EvaluationCommittee(
        assignment_id=assignment_id, formed_by=formed_by, status=CommitteeStatus.ACTIVE
    )
    db.add(committee)
    await db.flush()

    for m in members:
        db.add(CommitteeMember(
            committee_id=committee.id, evaluator_id=m.evaluator_id,
            role=m.role, is_external=m.is_external,
        ))
    await db.flush()
    logger.info("committee_formed", assignment=str(assignment_id), members=len(members))
    return committee
