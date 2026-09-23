from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.ti import (
    TICreateRequest, TIUpdateRequest, TIRead, TISummary, TIStatusSummary,
    MilestoneCreateRequest, MilestoneApproveRequest, MilestoneRead,
    AdvanceCreateRequest, AdvanceRead,
    AlertRead, AlertJustifyRequest,
)
from app.services.ti_service import (
    create_ti, update_ti, list_tis, _get_ti,
    add_milestone, approve_milestone,
    register_advance, run_delay_check, justify_alert,
    get_status_summary,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


# ── Research Works ────────────────────────────────────────────────────────────
@router.get("", summary="Listar TIs con filtros")
async def list_all(
    student_id: UUID | None = Query(None),
    tutor_id: UUID | None = Query(None),
    program_id: UUID | None = Query(None),
    ti_status: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","EST")),
    db: AsyncSession = Depends(get_db),
):
    total, items = await list_tis(db, student_id, tutor_id, program_id, ti_status, page, page_size)
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [TISummary(
            id=t.id, student_id=t.student_id, tutor_id=t.tutor_id,
            title=t.title, status=t.status, progress_percent=t.progress_percent,
            estimated_defense=t.estimated_defense,
            active_alerts=sum(1 for a in t.alerts if a.status == "active"),
        ) for t in items]
    }


@router.post("", response_model=TIRead, status_code=201, summary="Registrar nuevo TI")
async def create(
    data: TICreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","TUT")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return TIRead.model_validate(await create_ti(db, data))
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=TIStatusSummary, summary="Resumen KPI de TIs")
async def summary(
    program_id: UUID | None = Query(None),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return TIStatusSummary(**(await get_status_summary(db, program_id)))


@router.get("/{ti_id}", response_model=TIRead, summary="Ver TI completo")
async def get_one(
    ti_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","EST","CEV")),
    db: AsyncSession = Depends(get_db),
):
    ti = await _get_ti(db, ti_id)
    if not ti:
        raise HTTPException(status_code=404, detail="TI no encontrado.")
    return TIRead.model_validate(ti)


@router.patch("/{ti_id}", response_model=TIRead, summary="Actualizar TI")
async def update(
    ti_id: UUID,
    data: TIUpdateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","TUT","EST")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return TIRead.model_validate(await update_ti(db, ti_id, data, UUID(current_user.sub)))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Milestones ────────────────────────────────────────────────────────────────
@router.post("/milestones", response_model=MilestoneRead, status_code=201, summary="Añadir hito al cronograma")
async def add_milestone_ep(
    data: MilestoneCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","TUT")),
    db: AsyncSession = Depends(get_db),
):
    try:
        m = await add_milestone(db, data, UUID(current_user.sub))
        return MilestoneRead(
            id=m.id, name=m.name, milestone_type=m.milestone_type, status=m.status,
            planned_date=m.planned_date, actual_date=m.actual_date,
            weight_percent=m.weight_percent, is_critical=m.is_critical, approved_at=m.approved_at,
        )
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/milestones/{milestone_id}/approve", response_model=MilestoneRead, summary="Aprobar/rechazar hito")
async def approve_milestone_ep(
    milestone_id: UUID,
    data: MilestoneApproveRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","DIR","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        m = await approve_milestone(db, milestone_id, data, UUID(current_user.sub))
        return MilestoneRead(
            id=m.id, name=m.name, milestone_type=m.milestone_type, status=m.status,
            planned_date=m.planned_date, actual_date=m.actual_date,
            weight_percent=m.weight_percent, is_critical=m.is_critical, approved_at=m.approved_at,
        )
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)


# ── Progress ──────────────────────────────────────────────────────────────────
@router.post("/advances", response_model=AdvanceRead, status_code=201, summary="Registrar avance")
async def register_advance_ep(
    data: AdvanceCreateRequest,
    current_user: TokenPayload = Depends(require_roles("EST","TUT","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        a = await register_advance(db, data, UUID(current_user.sub))
        return AdvanceRead(
            id=a.id, period=a.period, activities_done=a.activities_done,
            progress_percent=a.progress_percent, obstacles=a.obstacles,
            action_plan=a.action_plan, registered_at=a.registered_at,
        )
    except (NotFoundError, ConflictError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 409, detail=e.message)


# ── Alerts ────────────────────────────────────────────────────────────────────
@router.post("/alerts/check", summary="Ejecutar verificación de retrasos (cron)")
async def trigger_delay_check(
    current_user: TokenPayload = Depends(require_roles("ADM","COO")),
    db: AsyncSession = Depends(get_db),
):
    return await run_delay_check(db)


@router.post("/alerts/{alert_id}/justify", response_model=AlertRead, summary="Justificar alerta de retraso")
async def justify_alert_ep(
    alert_id: UUID,
    data: AlertJustifyRequest,
    current_user: TokenPayload = Depends(require_roles("TUT","COO","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        a = await justify_alert(db, alert_id, data, UUID(current_user.sub))
        return AlertRead(id=a.id, level=a.level, reason=a.reason,
                        status=a.status, detected_at=a.detected_at, resolved_at=a.resolved_at)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
