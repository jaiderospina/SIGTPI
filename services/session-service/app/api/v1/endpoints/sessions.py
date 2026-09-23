from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.session import (
    SessionCreateRequest, SessionUpdateRequest, SessionCancelRequest,
    SessionRead, SessionSummary, VirtualRoomResponse,
    MinutesCreateRequest, MinutesStudentResponse, MinutesRead,
)
from app.services.session_service import (
    create_session, update_session, cancel_session,
    mark_completed, list_sessions, _get_session,
    create_minutes, student_respond_minutes, close_minutes_unilaterally,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.get("", summary="Listar sesiones")
async def list_all(
    ti_id: UUID | None = Query(None),
    tutor_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    session_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","EST")),
    db: AsyncSession = Depends(get_db),
):
    total, items = await list_sessions(db, ti_id, tutor_id, student_id, session_status, page, page_size)
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [SessionSummary(
            id=s.id, ti_id=s.ti_id, scheduled_at=s.scheduled_at,
            modality=s.modality, status=s.status,
            has_minutes=s.minutes is not None,
            meeting_url=s.meeting_url,
        ) for s in items]
    }


@router.post("", response_model=SessionRead, status_code=201, summary="Programar sesión de tutoría")
async def create(
    data: SessionCreateRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","ADM","EST")),
    db: AsyncSession = Depends(get_db),
):
    try:
        s = await create_session(db, data, UUID(current_user.sub))
        return SessionRead.model_validate(s)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}", response_model=SessionRead, summary="Ver sesión completa")
async def get_one(
    session_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","EST")),
    db: AsyncSession = Depends(get_db),
):
    s = await _get_session(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    return SessionRead.model_validate(s)


@router.patch("/{session_id}", response_model=SessionRead, summary="Actualizar sesión")
async def update(
    session_id: UUID, data: SessionUpdateRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return SessionRead.model_validate(
            await update_session(db, session_id, data, UUID(current_user.sub))
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)


@router.post("/{session_id}/cancel", response_model=SessionRead, summary="Cancelar sesión")
async def cancel(
    session_id: UUID, data: SessionCancelRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","ADM","EST")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return SessionRead.model_validate(
            await cancel_session(db, session_id, data, UUID(current_user.sub))
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)


@router.post("/{session_id}/complete", response_model=SessionRead, summary="Marcar sesión como completada")
async def complete(
    session_id: UUID,
    current_user: TokenPayload = Depends(require_roles("TUT","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return SessionRead.model_validate(
            await mark_completed(db, session_id, UUID(current_user.sub))
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/room", response_model=VirtualRoomResponse, summary="Obtener sala virtual")
async def get_room(
    session_id: UUID,
    current_user: TokenPayload = Depends(require_roles("TUT","EST","ADM")),
    db: AsyncSession = Depends(get_db),
):
    s = await _get_session(db, session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sesión no encontrada.")
    if not s.meeting_url:
        raise HTTPException(status_code=400, detail="Esta sesión no tiene sala virtual asignada.")
    return VirtualRoomResponse(room_id=s.meeting_room_id, meeting_url=s.meeting_url)


# ── Minutes ───────────────────────────────────────────────────────────────────
@router.post("/minutes", response_model=MinutesRead, status_code=201, summary="Registrar acta de sesión")
async def create_minutes_ep(
    data: MinutesCreateRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        m = await create_minutes(db, data, UUID(current_user.sub))
        return MinutesRead(
            id=m.id, session_id=m.session_id, topics_covered=m.topics_covered,
            agreements=m.agreements, commitments=m.commitments or [],
            tutor_observations=m.tutor_observations, student_observations=m.student_observations,
            status=m.status, tutor_signed_at=m.tutor_signed_at,
            student_signed_at=m.student_signed_at, dispute_reason=m.dispute_reason,
            registered_at=m.registered_at,
        )
    except (NotFoundError, ConflictError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else (409 if isinstance(e, ConflictError) else 403)
        raise HTTPException(status_code=code, detail=e.message)


@router.post("/minutes/{minutes_id}/respond", response_model=MinutesRead, summary="Confirmar o disputar acta")
async def respond_minutes(
    minutes_id: UUID, data: MinutesStudentResponse,
    current_user: TokenPayload = Depends(require_roles("EST")),
    db: AsyncSession = Depends(get_db),
):
    try:
        m = await student_respond_minutes(db, minutes_id, data, UUID(current_user.sub))
        return MinutesRead(
            id=m.id, session_id=m.session_id, topics_covered=m.topics_covered,
            agreements=m.agreements, commitments=m.commitments or [],
            tutor_observations=m.tutor_observations, student_observations=m.student_observations,
            status=m.status, tutor_signed_at=m.tutor_signed_at,
            student_signed_at=m.student_signed_at, dispute_reason=m.dispute_reason,
            registered_at=m.registered_at,
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)


@router.post("/minutes/{minutes_id}/close", response_model=MinutesRead, summary="Cerrar acta unilateralmente")
async def close_minutes(
    minutes_id: UUID,
    current_user: TokenPayload = Depends(require_roles("TUT","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        m = await close_minutes_unilaterally(db, minutes_id, UUID(current_user.sub))
        return MinutesRead(
            id=m.id, session_id=m.session_id, topics_covered=m.topics_covered,
            agreements=m.agreements, commitments=m.commitments or [],
            tutor_observations=m.tutor_observations, student_observations=m.student_observations,
            status=m.status, tutor_signed_at=m.tutor_signed_at,
            student_signed_at=m.student_signed_at, dispute_reason=m.dispute_reason,
            registered_at=m.registered_at,
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)
