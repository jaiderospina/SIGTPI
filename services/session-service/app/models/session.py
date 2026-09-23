import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, DateTime, Integer, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import SessionModality, SessionStatus, MinutesStatus


class TutoringSession(Base):
    __tablename__ = "tutoring_sessions"
    __table_args__ = {"schema": "sessions"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ti_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    tutor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    modality: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default=SessionStatus.SCHEDULED, nullable=False
    )
    agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
    meeting_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    meeting_room_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    rescheduled_from: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    minutes: Mapped["SessionMinutes | None"] = relationship(
        "SessionMinutes", back_populates="session", uselist=False, lazy="noload"
    )


class SessionMinutes(Base):
    """Acta de sesión de tutoría."""
    __tablename__ = "session_minutes"
    __table_args__ = {"schema": "sessions"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.tutoring_sessions.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    topics_covered: Mapped[str] = mapped_column(Text, nullable=False)
    agreements: Mapped[str | None] = mapped_column(Text, nullable=True)
    commitments: Mapped[list | None] = mapped_column(JSONB, nullable=True, default=list)
    tutor_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    student_observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=MinutesStatus.DRAFT, nullable=False
    )
    tutor_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    student_signed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    dispute_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session: Mapped["TutoringSession"] = relationship("TutoringSession", back_populates="minutes")
