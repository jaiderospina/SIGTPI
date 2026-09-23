from uuid import UUID
from datetime import datetime, date, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.models.ti import ResearchWork
from app.models.milestone import Milestone, ProgressAdvance, DelayAlert
from app.models.enums import TIStatus, MilestoneStatus, AlertStatus
from app.schemas.ti import (
    TICreateRequest, TIUpdateRequest,
    MilestoneCreateRequest, MilestoneApproveRequest,
    AdvanceCreateRequest, AlertJustifyRequest,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)

# Alert thresholds (days)
L1_DAYS_BEFORE = 7
L2_DAYS_AFTER  = 0
L3_DAYS_AFTER  = 14
L4_DAYS_AFTER  = 30


async def _get_ti(db: AsyncSession, ti_id: UUID) -> ResearchWork | None:
    r = await db.execute(
        select(ResearchWork)
        .options(
            selectinload(ResearchWork.milestones),
            selectinload(ResearchWork.advances),
            selectinload(ResearchWork.alerts),
        )
        .where(ResearchWork.id == ti_id)
    )
    return r.scalar_one_or_none()


# ── TI CRUD ───────────────────────────────────────────────────────────────────
async def create_ti(db: AsyncSession, data: TICreateRequest) -> ResearchWork:
    existing = (await db.execute(
        select(ResearchWork).where(ResearchWork.assignment_id == data.assignment_id)
    )).scalar_one_or_none()
    if existing:
        raise ConflictError("Ya existe un TI para esta asignación.")
    ti = ResearchWork(**data.model_dump())
    db.add(ti)
    await db.flush()
    # Auto-create standard milestones
    standard_milestones = [
        ("Aprobación de Anteproyecto", "anteproject_approval", True, 10.0),
        ("Primer Avance Semestral",    "semester_advance",     False, 15.0),
        ("Borrador Final",             "final_draft",          True, 25.0),
        ("Defensa Preliminar",         "preliminary_defense",  True, 20.0),
        ("Defensa Final",              "final_defense",        True, 30.0),
    ]
    from datetime import date
    base = data.start_date or date.today()
    for i, (name, mtype, critical, weight) in enumerate(standard_milestones):
        db.add(Milestone(
            ti_id=ti.id, name=name, milestone_type=mtype,
            planned_date=base + timedelta(days=90*(i+1)),
            weight_percent=weight, is_critical=critical,
        ))
    await db.flush()
    logger.info("ti_created", ti_id=str(ti.id), title=ti.title)
    return ti


async def update_ti(db: AsyncSession, ti_id: UUID, data: TIUpdateRequest, by: UUID) -> ResearchWork:
    ti = await _get_ti(db, ti_id)
    if not ti:
        raise NotFoundError("TI", ti_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(ti, field, value)
    ti.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return ti


async def list_tis(
    db: AsyncSession,
    student_id: UUID | None = None, tutor_id: UUID | None = None,
    program_id: UUID | None = None, status: str | None = None,
    page: int = 1, page_size: int = 20,
) -> tuple[int, list[ResearchWork]]:
    q = select(ResearchWork).options(
        selectinload(ResearchWork.milestones),
        selectinload(ResearchWork.alerts),
    )
    if student_id: q = q.where(ResearchWork.student_id == student_id)
    if tutor_id:   q = q.where(ResearchWork.tutor_id   == tutor_id)
    if program_id: q = q.where(ResearchWork.program_id == program_id)
    if status:     q = q.where(ResearchWork.status     == status)
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
    return total, list(items)


# ── MILESTONES ────────────────────────────────────────────────────────────────
async def add_milestone(db: AsyncSession, data: MilestoneCreateRequest, by: UUID) -> Milestone:
    ti = await _get_ti(db, data.ti_id)
    if not ti:
        raise NotFoundError("TI", data.ti_id)
    m = Milestone(**data.model_dump())
    db.add(m)
    await db.flush()
    return m


async def approve_milestone(
    db: AsyncSession, milestone_id: UUID, data: MilestoneApproveRequest, by: UUID
) -> Milestone:
    r = await db.execute(select(Milestone).where(Milestone.id == milestone_id))
    m = r.scalar_one_or_none()
    if not m:
        raise NotFoundError("Hito", milestone_id)
    if m.status not in [MilestoneStatus.PENDING, MilestoneStatus.IN_REVIEW]:
        raise ForbiddenError(f"No se puede aprobar un hito en estado '{m.status}'.")
    now = datetime.now(timezone.utc)
    if data.approved:
        m.status = MilestoneStatus.APPROVED.value
        m.actual_date = now.date()
        m.approved_by = by
        m.approved_at = now
        # Recalculate TI progress
        ti = await _get_ti(db, m.ti_id)
        if ti:
            approved_weight = sum(x.weight_percent for x in ti.milestones if x.status == MilestoneStatus.APPROVED)
            ti.progress_percent = min(round(approved_weight, 1), 100.0)
            ti.updated_at = now
    else:
        m.status = MilestoneStatus.REJECTED.value
        m.rejection_notes = data.rejection_notes
    await db.flush()
    return m


# ── PROGRESS ADVANCES ─────────────────────────────────────────────────────────
async def register_advance(db: AsyncSession, data: AdvanceCreateRequest, by: UUID) -> ProgressAdvance:
    ti = await _get_ti(db, data.ti_id)
    if not ti:
        raise NotFoundError("TI", data.ti_id)
    # Check for duplicate period
    if any(a.period == data.period for a in ti.advances):
        raise ConflictError(f"Ya existe un avance para el periodo {data.period}.")
    advance = ProgressAdvance(**data.model_dump(), registered_by=by)
    db.add(advance)
    # Update TI progress if higher
    if data.progress_percent > ti.progress_percent:
        ti.progress_percent = data.progress_percent
        ti.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("advance_registered", ti_id=str(data.ti_id), period=data.period, progress=data.progress_percent)
    return advance


# ── DELAY ALERTS ──────────────────────────────────────────────────────────────
async def run_delay_check(db: AsyncSession) -> dict:
    """Cron job: detecta retrasos y genera alertas escalonadas."""
    today = date.today()
    created = resolved = 0

    # Find all pending/in_review milestones
    r = await db.execute(
        select(Milestone)
        .options(selectinload(Milestone.ti))
        .where(Milestone.status.in_([MilestoneStatus.PENDING, MilestoneStatus.IN_REVIEW]))
    )
    milestones = r.scalars().all()

    for m in milestones:
        days_diff = (today - m.planned_date).days
        ti = m.ti

        # Determine alert level
        level = None
        if -L1_DAYS_BEFORE <= days_diff < 0:
            level = "1"
        elif days_diff >= L2_DAYS_AFTER and days_diff < L3_DAYS_AFTER:
            level = "2"
        elif days_diff >= L3_DAYS_AFTER and days_diff < L4_DAYS_AFTER:
            level = "3"
            m.status = MilestoneStatus.OVERDUE.value
        elif days_diff >= L4_DAYS_AFTER:
            level = "4"
            m.status = MilestoneStatus.OVERDUE.value

        if level:
            # Check if alert already exists at this level
            existing = (await db.execute(
                select(DelayAlert).where(
                    and_(DelayAlert.ti_id == ti.id,
                         DelayAlert.milestone_id == m.id,
                         DelayAlert.level == level,
                         DelayAlert.status == "active")
                )
            )).scalar_one_or_none()

            if not existing:
                alert = DelayAlert(
                    ti_id=ti.id, milestone_id=m.id, level=level,
                    reason=f"Hito '{m.name}' con {days_diff} días de retraso."
                    if days_diff >= 0 else f"Hito '{m.name}' vence en {-days_diff} días.",
                    status="active",
                )
                db.add(alert)
                ti.updated_at = datetime.now(timezone.utc)
                created += 1

    await db.flush()
    logger.info("delay_check_run", alerts_created=created)
    return {"alerts_created": created, "milestones_checked": len(milestones)}


async def justify_alert(
    db: AsyncSession, alert_id: UUID, data: AlertJustifyRequest, by: UUID
) -> DelayAlert:
    r = await db.execute(select(DelayAlert).where(DelayAlert.id == alert_id))
    alert = r.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alerta", alert_id)
    alert.status = "justified"
    alert.justification = data.justification
    alert.resolved_at = datetime.now(timezone.utc)
    await db.flush()
    return alert


# ── KPIs ──────────────────────────────────────────────────────────────────────
async def get_status_summary(db: AsyncSession, program_id: UUID | None = None) -> dict:
    q = select(ResearchWork)
    if program_id:
        q = q.where(ResearchWork.program_id == program_id)
    tis = (await db.execute(q.options(
        selectinload(ResearchWork.alerts),
        selectinload(ResearchWork.milestones),
    ))).scalars().all()

    by_status: dict[str, int] = {}
    at_risk = overdue_milestones = 0
    total_progress = 0.0

    for ti in tis:
        by_status[ti.status] = by_status.get(ti.status, 0) + 1
        active_alerts = [a for a in ti.alerts if a.status == "active"]
        if any(a.level in ["3","4"] for a in active_alerts):
            at_risk += 1
        overdue_milestones += sum(1 for m in ti.milestones if m.status == MilestoneStatus.OVERDUE)
        total_progress += ti.progress_percent

    return {
        "total": len(tis),
        "by_status": by_status,
        "at_risk": at_risk,
        "overdue_milestones": overdue_milestones,
        "avg_progress": round(total_progress / len(tis), 1) if tis else 0.0,
    }
