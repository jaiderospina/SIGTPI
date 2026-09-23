from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.rubric import Rubric
from app.models.evaluation import Evaluation, IndividualScore
from app.models.enums import EvaluationStatus, Dictamen
from app.schemas.evaluation import (
    RubricCreateRequest, EvaluationCreateRequest,
    IndividualScoreSubmit, DictamenRequest,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


async def create_rubric(db: AsyncSession, data: RubricCreateRequest, by: UUID) -> Rubric:
    rubric = Rubric(
        program_id=data.program_id, evaluation_type=data.evaluation_type,
        name=data.name, description=data.description,
        criteria=[c.model_dump() for c in data.criteria], created_by=by,
    )
    db.add(rubric)
    await db.flush()
    logger.info("rubric_created", name=data.name, type=data.evaluation_type)
    return rubric


async def list_rubrics(db: AsyncSession, evaluation_type: str | None = None,
                       program_id: UUID | None = None) -> list[Rubric]:
    q = select(Rubric).where(Rubric.is_active == True)
    if evaluation_type: q = q.where(Rubric.evaluation_type == evaluation_type)
    if program_id: q = q.where(Rubric.program_id == program_id)
    return list((await db.execute(q)).scalars().all())


async def create_evaluation(db: AsyncSession, data: EvaluationCreateRequest, by: UUID) -> Evaluation:
    rubric = (await db.execute(select(Rubric).where(Rubric.id == data.rubric_id))).scalar_one_or_none()
    if not rubric:
        raise NotFoundError("Rúbrica", data.rubric_id)
    existing = (await db.execute(
        select(Evaluation).where(
            Evaluation.ti_id == data.ti_id,
            Evaluation.evaluation_type == data.evaluation_type,
            Evaluation.status != EvaluationStatus.PUBLISHED,
        )
    )).scalar_one_or_none()
    if existing:
        raise ConflictError("Ya existe una evaluación activa de ese tipo para este TI.")
    ev = Evaluation(
        ti_id=data.ti_id, milestone_id=data.milestone_id,
        rubric_id=data.rubric_id, evaluation_type=data.evaluation_type,
    )
    db.add(ev)
    await db.flush()
    return ev


async def submit_individual_score(
    db: AsyncSession, data: IndividualScoreSubmit, evaluator_id: UUID
) -> IndividualScore:
    ev_r = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.individual_scores))
        .where(Evaluation.id == data.evaluation_id)
    )
    ev = ev_r.scalar_one_or_none()
    if not ev:
        raise NotFoundError("Evaluación", data.evaluation_id)
    if ev.status == EvaluationStatus.PUBLISHED:
        raise ForbiddenError("La evaluación ya fue publicada.")
    # Check duplicate
    if any(s.evaluator_id == evaluator_id for s in ev.individual_scores):
        raise ConflictError("Ya enviaste tu evaluación para esta sesión.")
    # Load rubric to compute weighted average
    rubric = (await db.execute(select(Rubric).where(Rubric.id == ev.rubric_id))).scalar_one_or_none()
    weighted = 0.0
    if rubric:
        for criterion in rubric.criteria:
            cid = criterion["id"]
            weight = criterion["weight"]
            score = data.scores.get(cid, 0.0)
            weighted += score * weight
    score_rec = IndividualScore(
        evaluation_id=data.evaluation_id, evaluator_id=evaluator_id,
        scores=data.scores, weighted_average=round(weighted, 2),
        qualitative_feedback=data.qualitative_feedback,
        strengths=data.strengths, improvements=data.improvements,
    )
    db.add(score_rec)
    ev.status = EvaluationStatus.SUBMITTED.value
    await db.flush()
    logger.info("score_submitted", evaluation=str(data.evaluation_id), evaluator=str(evaluator_id))
    return score_rec


async def issue_dictamen(
    db: AsyncSession, evaluation_id: UUID, data: DictamenRequest, by: UUID
) -> Evaluation:
    ev_r = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.individual_scores))
        .where(Evaluation.id == evaluation_id)
    )
    ev = ev_r.scalar_one_or_none()
    if not ev:
        raise NotFoundError("Evaluación", evaluation_id)
    if ev.status == EvaluationStatus.PUBLISHED:
        raise ForbiddenError("La evaluación ya fue publicada.")
    if not ev.individual_scores:
        raise ForbiddenError("No hay evaluaciones individuales registradas.")
    # Compute consolidated grade as average of individual weighted averages
    avg = sum(s.weighted_average for s in ev.individual_scores) / len(ev.individual_scores)
    ev.consolidated_grade = round(avg, 2)
    ev.dictamen = data.dictamen
    ev.consolidated_feedback = data.consolidated_feedback
    ev.status = EvaluationStatus.PUBLISHED.value
    ev.issued_by = by
    ev.issued_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("dictamen_issued", evaluation=str(evaluation_id), dictamen=data.dictamen)
    return ev


async def get_evaluation(db: AsyncSession, evaluation_id: UUID) -> Evaluation | None:
    r = await db.execute(
        select(Evaluation)
        .options(selectinload(Evaluation.individual_scores))
        .where(Evaluation.id == evaluation_id)
    )
    return r.scalar_one_or_none()
