from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.report import (
    DashboardSummary, TIStatusKPI,
    TutorWorkloadKPI, ProgramKPI, StudentProgressReport,
)
from app.services.report_service import (
    get_dashboard_summary, get_ti_status_kpi,
    get_tutor_workload, get_program_kpis, get_student_report,
)
from sigtpi_common.security.jwt import TokenPayload

router = APIRouter()


@router.get("/dashboard", response_model=DashboardSummary, summary="Dashboard ejecutivo")
async def dashboard(
    program_id: UUID | None = Query(None),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_summary(db, program_id)


@router.get("/ti/status", response_model=TIStatusKPI, summary="KPIs de estado de TIs")
async def ti_status(
    program_id: UUID | None = Query(None),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return await get_ti_status_kpi(db, program_id)


@router.get("/tutors/{tutor_id}/workload", response_model=TutorWorkloadKPI)
async def tutor_workload(
    tutor_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return await get_tutor_workload(db, tutor_id)


@router.get("/programs/{program_id}", response_model=ProgramKPI)
async def program_kpis(
    program_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return await get_program_kpis(db, program_id)


@router.get("/students/{student_id}", response_model=StudentProgressReport)
async def student_report(
    student_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","EST")),
    db: AsyncSession = Depends(get_db),
):
    return await get_student_report(db, student_id)
