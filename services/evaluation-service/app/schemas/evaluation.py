from uuid import UUID
from datetime import datetime
from pydantic import Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import EvaluationType, Dictamen, EvaluationStatus


class CriterionDefinition(BaseSchema):
    id: str
    name: str
    weight: float = Field(..., gt=0, le=1.0)
    descriptors: dict[str, str] = {}  # {"5":"Excelente","4":"Bueno",...}


class RubricCreateRequest(BaseSchema):
    program_id: UUID | None = None
    evaluation_type: EvaluationType
    name: str = Field(..., min_length=3)
    description: str | None = None
    criteria: list[CriterionDefinition]

    @field_validator("criteria")
    @classmethod
    def weights_must_sum_one(cls, v):
        total = sum(c.weight for c in v)
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Los pesos deben sumar 1.0 (actual: {total:.2f})")
        return v


class RubricRead(IdentifiedSchema):
    program_id: UUID | None
    evaluation_type: str
    name: str
    description: str | None
    is_active: bool
    criteria: list[dict]


class EvaluationCreateRequest(BaseSchema):
    ti_id: UUID
    milestone_id: UUID | None = None
    rubric_id: UUID
    evaluation_type: EvaluationType


class IndividualScoreSubmit(BaseSchema):
    evaluation_id: UUID
    scores: dict[str, float]
    qualitative_feedback: str | None = None
    strengths: str | None = None
    improvements: str | None = None


class IndividualScoreRead(BaseSchema):
    id: UUID
    evaluator_id: UUID
    scores: dict
    weighted_average: float
    qualitative_feedback: str | None
    strengths: str | None
    improvements: str | None
    submitted_at: datetime


class DictamenRequest(BaseSchema):
    dictamen: Dictamen
    consolidated_feedback: str = Field(..., min_length=20)


class EvaluationRead(IdentifiedSchema):
    ti_id: UUID
    milestone_id: UUID | None
    rubric_id: UUID
    evaluation_type: str
    status: str
    consolidated_grade: float | None
    dictamen: str
    consolidated_feedback: str | None
    issued_at: datetime | None
    individual_scores: list[IndividualScoreRead] = []
