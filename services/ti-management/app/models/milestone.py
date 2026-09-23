import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Date, Text, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import MilestoneType, MilestoneStatus


class Milestone(Base):
    """Hito del cronograma del TI."""
    __tablename__ = "milestones"
    __table_args__ = {"schema": "ti"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ti.research_works.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    milestone_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=MilestoneStatus.PENDING, nullable=False
    )
    planned_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    weight_percent: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    ti: Mapped["ResearchWork"] = relationship("ResearchWork", back_populates="milestones")  # type: ignore


class ProgressAdvance(Base):
    """Registro de avance periódico del estudiante."""
    __tablename__ = "progress_advances"
    __table_args__ = {"schema": "ti"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ti.research_works.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(String(20), nullable=False)  # "2024-1"
    activities_done: Mapped[str] = mapped_column(Text, nullable=False)
    progress_percent: Mapped[float] = mapped_column(Float, nullable=False)
    obstacles: Mapped[str | None] = mapped_column(Text, nullable=True)
    action_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    registered_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    ti: Mapped["ResearchWork"] = relationship("ResearchWork", back_populates="advances")  # type: ignore


class DelayAlert(Base):
    """Alerta de retraso escalonada (niveles 1-4)."""
    __tablename__ = "delay_alerts"
    __table_args__ = {"schema": "ti"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ti.research_works.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    milestone_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    level: Mapped[str] = mapped_column(String(1), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    justification: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    ti: Mapped["ResearchWork"] = relationship("ResearchWork", back_populates="alerts")  # type: ignore
