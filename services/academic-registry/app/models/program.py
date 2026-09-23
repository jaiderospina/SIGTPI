import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import ProgramLevel, ProgramStatus


class Program(Base):
    __tablename__ = "programs"
    __table_args__ = {"schema": "academic"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    level: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    duration_semesters: Mapped[int | None] = mapped_column(nullable=True)
    duration_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_students_per_tutor: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    min_gpa_for_ti: Mapped[float] = mapped_column(default=3.5, nullable=False)
    description: Mapped[str | None]
    coordinator_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=ProgramStatus.ACTIVE, nullable=False
    )
    director_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment", back_populates="program", lazy="noload"
    )
