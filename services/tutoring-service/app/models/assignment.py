import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import AssignmentStatus


class TutorAssignment(Base):
    """Asignación de tutor principal a un trabajo de investigación."""
    __tablename__ = "tutor_assignments"
    __table_args__ = {"schema": "tutoring"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tutor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    research_area: Mapped[str] = mapped_column(String(255), nullable=False)
    preliminary_title: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=AssignmentStatus.PENDING, nullable=False
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    responded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    co_tutors: Mapped[list["CoTutor"]] = relationship(
        "CoTutor", back_populates="assignment", lazy="select", cascade="all, delete-orphan"
    )


class CoTutor(Base):
    """Co-tutor asignado a un trabajo de investigación."""
    __tablename__ = "co_tutors"
    __table_args__ = (
        UniqueConstraint("assignment_id", "tutor_id", name="uq_cotutor_assignment"),
        {"schema": "tutoring"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutoring.tutor_assignments.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    tutor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    area_of_contribution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    assignment: Mapped["TutorAssignment"] = relationship("TutorAssignment", back_populates="co_tutors")
