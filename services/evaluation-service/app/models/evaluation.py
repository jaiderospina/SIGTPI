import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import EvaluationType, Dictamen, EvaluationStatus


class Evaluation(Base):
    """Evaluación formal de un TI en un hito."""
    __tablename__ = "evaluations"
    __table_args__ = {"schema": "evaluation"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    rubric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation.rubrics.id"), nullable=False
    )
    evaluation_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=EvaluationStatus.DRAFT, nullable=False
    )
    consolidated_grade: Mapped[float | None] = mapped_column(Float, nullable=True)
    dictamen: Mapped[str] = mapped_column(
        String(50),
        default=Dictamen.PENDING, nullable=False
    )
    consolidated_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    rubric: Mapped["Rubric"] = relationship("Rubric", back_populates="evaluations")  # type: ignore
    individual_scores: Mapped[list["IndividualScore"]] = relationship(
        "IndividualScore", back_populates="evaluation",
        lazy="noload", cascade="all, delete-orphan"
    )


class IndividualScore(Base):
    """Evaluación individual de un miembro del comité."""
    __tablename__ = "individual_scores"
    __table_args__ = {"schema": "evaluation"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluation.evaluations.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    evaluator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    scores: Mapped[dict] = mapped_column(JSONB, nullable=False)
    # scores: {"c1": 4.5, "c2": 3.8, ...}
    weighted_average: Mapped[float] = mapped_column(Float, nullable=False)
    qualitative_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    improvements: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    evaluation: Mapped["Evaluation"] = relationship("Evaluation", back_populates="individual_scores")
