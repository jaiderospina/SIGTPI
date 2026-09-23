import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Text, Float, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import TIStatus, KnowledgeArea


class ResearchWork(Base):
    """Trabajo de Investigación (TI) — entidad central del sistema."""
    __tablename__ = "research_works"
    __table_args__ = {"schema": "ti"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tutor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    knowledge_area: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    problem_statement: Mapped[str | None] = mapped_column(Text, nullable=True)
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    methodology: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)

    status: Mapped[str] = mapped_column(
        String(50),
        default=TIStatus.DRAFT, nullable=False
    )
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    estimated_defense: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_defense: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    milestones: Mapped[list["Milestone"]] = relationship(
        "Milestone", back_populates="ti", lazy="selectin",
        cascade="all, delete-orphan", order_by="Milestone.planned_date"
    )
    advances: Mapped[list["ProgressAdvance"]] = relationship(
        "ProgressAdvance", back_populates="ti", lazy="selectin",
        cascade="all, delete-orphan", order_by="ProgressAdvance.registered_at.desc()"
    )
    alerts: Mapped[list["DelayAlert"]] = relationship(
        "DelayAlert", back_populates="ti", lazy="selectin",
        cascade="all, delete-orphan"
    )
