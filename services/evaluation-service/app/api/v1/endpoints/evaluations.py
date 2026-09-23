from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.evaluation import (
    RubricCreateRequest, RubricRead,
    EvaluationCreateRequest, EvaluationRead,
    IndividualScoreSubmit, IndividualScoreRead,
    DictamenRequest,
)
from app.services.evaluation_service import (
    create_rubric, list_rubrics, create_evaluation,
    submit_individual_score, issue_dictamen, get_evaluation,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.get("/rubrics", response_model=list[RubricRead], summary="Listar rúbricas")
async def list_rubrics_ep(
    evaluation_type: str | None = Query(None),
    program_id: UUID | None = Query(None),
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","CEV")),
    db: AsyncSession = Depends(get_db),
):
    rubrics = await list_rubrics(db, evaluation_type, program_id)
    return [RubricRead.model_validate(r) for r in rubrics]


@router.post("/rubrics", response_model=RubricRead, status_code=201, summary="Crear rúbrica")
async def create_rubric_ep(
    data: RubricCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","DIR","COO")),
    db: AsyncSession = Depends(get_db),
):
    r = await create_rubric(db, data, UUID(current_user.sub))
    return RubricRead.model_validate(r)


@router.post("", response_model=EvaluationRead, status_code=201, summary="Iniciar evaluación")
async def create_evaluation_ep(
    data: EvaluationCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ev = await create_evaluation(db, data, UUID(current_user.sub))
        return EvaluationRead.model_validate(ev)
    except (NotFoundError, ConflictError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 409, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{evaluation_id}", response_model=EvaluationRead, summary="Ver evaluación")
async def get_one(
    evaluation_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT","CEV")),
    db: AsyncSession = Depends(get_db),
):
    ev = await get_evaluation(db, evaluation_id)
    if not ev:
        raise HTTPException(status_code=404, detail="Evaluación no encontrada.")
    return EvaluationRead.model_validate(ev)


@router.post("/scores", response_model=IndividualScoreRead, status_code=201,
             summary="Enviar evaluación individual de comité")
async def submit_score(
    data: IndividualScoreSubmit,
    current_user: TokenPayload = Depends(require_roles("CEV","TUT","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        s = await submit_individual_score(db, data, UUID(current_user.sub))
        return IndividualScoreRead(
            id=s.id, evaluator_id=s.evaluator_id, scores=s.scores,
            weighted_average=s.weighted_average, qualitative_feedback=s.qualitative_feedback,
            strengths=s.strengths, improvements=s.improvements, submitted_at=s.submitted_at,
        )
    except (NotFoundError, ConflictError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else (409 if isinstance(e, ConflictError) else 403)
        raise HTTPException(status_code=code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{evaluation_id}/dictamen", response_model=EvaluationRead, summary="Emitir dictamen oficial")
async def issue_dictamen_ep(
    evaluation_id: UUID,
    data: DictamenRequest,
    current_user: TokenPayload = Depends(require_roles("DIR","ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        ev = await issue_dictamen(db, evaluation_id, data, UUID(current_user.sub))
        return EvaluationRead.model_validate(ev)
    except (NotFoundError, ForbiddenError) as e:
        raise HTTPException(status_code=404 if isinstance(e, NotFoundError) else 403, detail=e.message)
