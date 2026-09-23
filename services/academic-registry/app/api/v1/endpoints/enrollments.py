from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.academic import (
    EnrollmentCreateRequest, EnrollmentUpdateRequest,
    EnrollmentRead, EnrollmentSummary,
    GradeSubmitRequest, SemesterGradeRead,
    PrerequisiteCheckRequest, PrerequisiteCheckResponse,
)
from app.services.academic_service import (
    list_enrollments, get_enrollment, create_enrollment,
    update_enrollment_status, submit_grade, approve_grade, check_prerequisites,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.get("", summary="Listar matrículas")
async def list_all(
    program_id: UUID | None = Query(None),
    cohort: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR", "TUT")),
    db: AsyncSession = Depends(get_db),
):
    total, items = await list_enrollments(db, program_id, cohort, status, page, page_size)
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [EnrollmentSummary(
            id=e.id, student_id=e.student_id, program_id=e.program_id,
            cohort=e.cohort, status=e.status, gpa=e.gpa, ti_approved=e.ti_approved,
        ) for e in items]
    }


@router.post("", response_model=EnrollmentRead, status_code=201, summary="Matricular estudiante")
async def enroll(
    data: EnrollmentCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return EnrollmentRead.model_validate(await create_enrollment(db, data))
    except (NotFoundError, ConflictError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else (409 if isinstance(e, ConflictError) else 403)
        raise HTTPException(status_code=code, detail=e.message)


@router.get("/{enrollment_id}", response_model=EnrollmentRead, summary="Obtener matrícula")
async def get_one(
    enrollment_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR", "TUT", "EST")),
    db: AsyncSession = Depends(get_db),
):
    e = await get_enrollment(db, enrollment_id)
    if not e:
        raise HTTPException(status_code=404, detail="Matrícula no encontrada.")
    return EnrollmentRead.model_validate(e)


@router.patch("/{enrollment_id}", response_model=EnrollmentRead, summary="Actualizar estado de matrícula")
async def update_status(
    enrollment_id: UUID,
    data: EnrollmentUpdateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return EnrollmentRead.model_validate(await update_enrollment_status(db, enrollment_id, data))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/grades", response_model=SemesterGradeRead, status_code=201, summary="Registrar calificación semestral")
async def submit_grade_endpoint(
    data: GradeSubmitRequest,
    current_user: TokenPayload = Depends(require_roles("TUT", "COO", "ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        g = await submit_grade(db, data, UUID(current_user.sub))
        return SemesterGradeRead(
            id=g.id, semester=g.semester, grade=g.grade, tutor_id=g.tutor_id,
            status=g.status, comments=g.comments, recorded_at=g.recorded_at,
        )
    except (NotFoundError, ConflictError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else (409 if isinstance(e, ConflictError) else 403)
        raise HTTPException(status_code=code, detail=e.message)


@router.post("/grades/{grade_id}/approve", response_model=SemesterGradeRead, summary="Aprobar calificación")
async def approve_grade_endpoint(
    grade_id: UUID,
    current_user: TokenPayload = Depends(require_roles("COO", "DIR", "ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        g = await approve_grade(db, grade_id, UUID(current_user.sub))
        return SemesterGradeRead(
            id=g.id, semester=g.semester, grade=g.grade, tutor_id=g.tutor_id,
            status=g.status, comments=g.comments, recorded_at=g.recorded_at,
        )
    except (NotFoundError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else 403
        raise HTTPException(status_code=code, detail=e.message)


@router.post("/prerequisites/check", response_model=PrerequisiteCheckResponse,
             summary="Verificar prerequisitos académicos")
async def check_prereqs(
    data: PrerequisiteCheckRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await check_prerequisites(db, data.student_id, data.program_id, data.check_type)
    return PrerequisiteCheckResponse(
        student_id=data.student_id,
        program_id=data.program_id,
        check_type=data.check_type,
        meets_requirements=result["meets_requirements"],
        details=result["details"],
    )
