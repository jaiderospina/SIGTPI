import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import CommitteeRole, CommitteeStatus


class EvaluationCommittee(Base):
    """Comité evaluador de un TI."""
    __tablename__ = "evaluation_committees"
    __table_args__ = {"schema": "tutoring"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assignment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=CommitteeStatus.FORMING, nullable=False
    )
    formed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    formed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    members: Mapped[list["CommitteeMember"]] = relationship(
        "CommitteeMember", back_populates="committee", lazy="noload", cascade="all, delete-orphan"
    )


class CommitteeMember(Base):
    """Miembro de un comité evaluador."""
    __tablename__ = "committee_members"
    __table_args__ = (
        UniqueConstraint("committee_id", "evaluator_id", name="uq_committee_member"),
        {"schema": "tutoring"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    committee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tutoring.evaluation_committees.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    evaluator_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    role: Mapped[str] = mapped_column(
        String(50),
        default=CommitteeRole.MEMBER, nullable=False
    )
    is_external: Mapped[bool] = mapped_column(default=False, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    committee: Mapped["EvaluationCommittee"] = relationship("EvaluationCommittee", back_populates="members")
