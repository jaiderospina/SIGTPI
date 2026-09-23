from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.tutoring import (
    AssignmentRequestCreate, AssignmentResponseRequest, AssignmentRead,
    AssignmentSummary, CoTutorAddRequest, CoTutorRead,
    CommitteeMemberAdd, CommitteeRead, TutorWorkloadResponse,
)
from app.services.tutoring_service import (
    create_assignment, respond_to_assignment, add_co_tutor,
    list_assignments, get_tutor_workload, create_committee,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.get("", summary="Listar asignaciones de tutoría")
async def list_all(
    tutor_id: UUID | None = Query(None),
    student_id: UUID | None = Query(None),
    status: str | None = Query(None),
    program_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT")),
    db: AsyncSession = Depends(get_db),
):
    total, items = await list_assignments(db, tutor_id, student_id, status, program_id, page, page_size)
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [AssignmentSummary(
            id=a.id, student_id=a.student_id, tutor_id=a.tutor_id,
            program_id=a.program_id, status=a.status, research_area=a.research_area,
        ) for a in items]
    }


@router.post("", response_model=AssignmentRead, status_code=201, summary="Crear asignación de tutor")
async def create(
    data: AssignmentRequestCreate,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        a = await create_assignment(db, data, UUID(current_user.sub))
        return AssignmentRead.model_validate(a)
    except (ConflictError, ForbiddenError) as e:
        raise HTTPException(status_code=409 if isinstance(e, ConflictError) else 403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{assignment_id}", response_model=AssignmentRead, summary="Ver asignación")
async def get_one(
    assignment_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.tutoring_service import _get_assignment
    a = await _get_assignment(db, assignment_id)
    if not a:
        raise HTTPException(status_code=404, detail="Asignación no encontrada.")
    return AssignmentRead.model_validate(a)


@router.post("/{assignment_id}/respond", response_model=AssignmentRead, summary="Aceptar o rechazar asignación")
async def respond(
    assignment_id: UUID,
    data: AssignmentResponseRequest,
    current_user: TokenPayload = Depends(require_roles("TUT")),
    db: AsyncSession = Depends(get_db),
):
    try:
        a = await respond_to_assignment(db, assignment_id, UUID(current_user.sub), data)
        return AssignmentRead.model_validate(a)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/co-tutors", response_model=CoTutorRead, status_code=201, summary="Añadir co-tutor")
async def add_co_tutor_endpoint(
    data: CoTutorAddRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ct = await add_co_tutor(db, data, UUID(current_user.sub))
        return CoTutorRead(id=ct.id, tutor_id=ct.tutor_id,
                           area_of_contribution=ct.area_of_contribution, added_at=ct.added_at)
    except (NotFoundError, ConflictError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else (409 if isinstance(e, ConflictError) else 403)
        raise HTTPException(status_code=code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tutor/{tutor_id}/workload", response_model=TutorWorkloadResponse, summary="Carga actual del tutor")
async def workload(
    tutor_id: UUID,
    max_students: int = Query(5, ge=1),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    return TutorWorkloadResponse(**(await get_tutor_workload(db, tutor_id, max_students)))


@router.post("/{assignment_id}/committee", response_model=CommitteeRead, status_code=201,
             summary="Conformar comité evaluador")
async def form_committee(
    assignment_id: UUID,
    members: list[CommitteeMemberAdd],
    current_user: TokenPayload = Depends(require_roles("ADM","DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        c = await create_committee(db, assignment_id, members, UUID(current_user.sub))
        return CommitteeRead.model_validate(c)
    except (NotFoundError, ConflictError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 409, detail=e.message)
