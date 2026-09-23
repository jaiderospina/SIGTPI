from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.session import TutoringSession, SessionMinutes
from app.models.enums import SessionStatus, MinutesStatus, SessionModality
from app.schemas.session import (
    SessionCreateRequest, SessionUpdateRequest, SessionCancelRequest,
    MinutesCreateRequest, MinutesStudentResponse,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


def _generate_room(session_id: UUID) -> tuple[str, str]:
    """Generate internal Jitsi room ID and URL."""
    room_id = f"sigtpi-{str(session_id)[:8]}"
    url = f"https://meet.sigtpi.local/{room_id}"
    return room_id, url


async def _get_session(db: AsyncSession, session_id: UUID) -> TutoringSession | None:
    r = await db.execute(
        select(TutoringSession)
        .options(selectinload(TutoringSession.minutes))
        .where(TutoringSession.id == session_id)
    )
    return r.scalar_one_or_none()


async def create_session(
    db: AsyncSession, data: SessionCreateRequest, created_by: UUID
) -> TutoringSession:
    # Prevent double-booking: same tutor within ±2 hours
    window_start = data.scheduled_at - timedelta(hours=2)
    window_end   = data.scheduled_at + timedelta(hours=2)
    conflict = (await db.execute(
        select(TutoringSession).where(
            and_(
                TutoringSession.tutor_id == data.tutor_id,
                TutoringSession.scheduled_at.between(window_start, window_end),
                TutoringSession.status.in_([SessionStatus.SCHEDULED, SessionStatus.CONFIRMED]),
            )
        )
    )).scalar_one_or_none()
    if conflict:
        raise ConflictError("El tutor ya tiene una sesión programada en ese horario.")

    session = TutoringSession(
        ti_id=data.ti_id, tutor_id=data.tutor_id, student_id=data.student_id,
        scheduled_at=data.scheduled_at, duration_minutes=data.duration_minutes,
        modality=data.modality, agenda=data.agenda, created_by=created_by,
    )

    # Auto-generate Jitsi room for virtual sessions
    if data.modality in [SessionModality.VIRTUAL, SessionModality.HYBRID]:
        room_id, url = _generate_room(session.id)
        session.meeting_room_id = room_id
        session.meeting_url = url

    db.add(session)
    await db.flush()
    logger.info("session_created", session_id=str(session.id), ti_id=str(data.ti_id))
    return session


async def update_session(
    db: AsyncSession, session_id: UUID, data: SessionUpdateRequest, by: UUID
) -> TutoringSession:
    session = await _get_session(db, session_id)
    if not session:
        raise NotFoundError("Sesión", session_id)
    if session.status not in [SessionStatus.SCHEDULED, SessionStatus.CONFIRMED]:
        raise ForbiddenError("Solo se pueden modificar sesiones programadas o confirmadas.")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(session, field, value)
    # Regenerate room if modality changed to virtual
    if data.modality in [SessionModality.VIRTUAL, SessionModality.HYBRID] and not session.meeting_url:
        room_id, url = _generate_room(session.id)
        session.meeting_room_id = room_id
        session.meeting_url = url
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def cancel_session(
    db: AsyncSession, session_id: UUID, data: SessionCancelRequest, by: UUID
) -> TutoringSession:
    session = await _get_session(db, session_id)
    if not session:
        raise NotFoundError("Sesión", session_id)
    if session.status in [SessionStatus.COMPLETED, SessionStatus.CANCELLED]:
        raise ForbiddenError(f"No se puede cancelar una sesión en estado '{session.status}'.")
    session.status = SessionStatus.CANCELLED.value
    session.cancellation_reason = data.reason
    session.cancelled_by = by
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("session_cancelled", session_id=str(session_id))
    return session


async def mark_completed(db: AsyncSession, session_id: UUID, by: UUID) -> TutoringSession:
    session = await _get_session(db, session_id)
    if not session:
        raise NotFoundError("Sesión", session_id)
    session.status = SessionStatus.COMPLETED.value
    session.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return session


async def list_sessions(
    db: AsyncSession,
    ti_id: UUID | None = None, tutor_id: UUID | None = None,
    student_id: UUID | None = None, status: str | None = None,
    page: int = 1, page_size: int = 20,
) -> tuple[int, list[TutoringSession]]:
    q = select(TutoringSession).options(selectinload(TutoringSession.minutes))
    if ti_id:      q = q.where(TutoringSession.ti_id      == ti_id)
    if tutor_id:   q = q.where(TutoringSession.tutor_id   == tutor_id)
    if student_id: q = q.where(TutoringSession.student_id == student_id)
    if status:     q = q.where(TutoringSession.status      == status)
    q = q.order_by(TutoringSession.scheduled_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
    return total, list(items)


# ── MINUTES ───────────────────────────────────────────────────────────────────
async def create_minutes(
    db: AsyncSession, data: MinutesCreateRequest, tutor_id: UUID
) -> SessionMinutes:
    session = await _get_session(db, data.session_id)
    if not session:
        raise NotFoundError("Sesión", data.session_id)
    if session.status != SessionStatus.COMPLETED:
        raise ForbiddenError("Solo se pueden registrar actas de sesiones completadas.")
    if session.tutor_id != tutor_id:
        raise ForbiddenError("Solo el tutor puede registrar el acta.")
    if session.minutes:
        raise ConflictError("Esta sesión ya tiene un acta registrada.")

    now = datetime.now(timezone.utc)
    minutes = SessionMinutes(
        session_id=data.session_id,
        topics_covered=data.topics_covered,
        agreements=data.agreements,
        commitments=[c.model_dump() for c in data.commitments],
        tutor_observations=data.tutor_observations,
        status=MinutesStatus.PENDING,
        tutor_signed_at=now,
    )
    db.add(minutes)
    await db.flush()
    logger.info("minutes_created", session_id=str(data.session_id))
    return minutes


async def student_respond_minutes(
    db: AsyncSession, minutes_id: UUID, data: MinutesStudentResponse, student_id: UUID
) -> SessionMinutes:
    r = await db.execute(
        select(SessionMinutes)
        .options(selectinload(SessionMinutes.session))
        .where(SessionMinutes.id == minutes_id)
    )
    minutes = r.scalar_one_or_none()
    if not minutes:
        raise NotFoundError("Acta", minutes_id)
    if minutes.session.student_id != student_id:
        raise ForbiddenError("Solo el estudiante puede confirmar el acta.")
    if minutes.status != MinutesStatus.PENDING:
        raise ForbiddenError(f"El acta no está pendiente de confirmación (estado: {minutes.status}).")

    now = datetime.now(timezone.utc)
    if data.confirm:
        minutes.status = MinutesStatus.CONFIRMED.value
        minutes.student_signed_at = now
    else:
        if not data.dispute_reason:
            raise ForbiddenError("Debe indicar el motivo de la objeción.")
        minutes.status = MinutesStatus.DISPUTED.value
        minutes.dispute_reason = data.dispute_reason
    minutes.student_observations = data.student_observations
    await db.flush()
    logger.info("minutes_responded", minutes_id=str(minutes_id), confirmed=data.confirm)
    return minutes


async def close_minutes_unilaterally(
    db: AsyncSession, minutes_id: UUID, tutor_id: UUID
) -> SessionMinutes:
    """Tutor closes minutes if student hasn't confirmed in 72h."""
    r = await db.execute(
        select(SessionMinutes)
        .options(selectinload(SessionMinutes.session))
        .where(SessionMinutes.id == minutes_id)
    )
    minutes = r.scalar_one_or_none()
    if not minutes:
        raise NotFoundError("Acta", minutes_id)
    if minutes.session.tutor_id != tutor_id:
        raise ForbiddenError("Solo el tutor puede cerrar el acta unilateralmente.")
    if minutes.status != MinutesStatus.PENDING:
        raise ForbiddenError("El acta no está pendiente.")
    minutes.status = MinutesStatus.CLOSED.value
    await db.flush()
    logger.info("minutes_closed_unilaterally", minutes_id=str(minutes_id))
    return minutes
