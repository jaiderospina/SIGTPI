import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, Date, ForeignKey, Float, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import StudentStatus, SemesterGradeStatus


class Enrollment(Base):
    """Matrícula de un estudiante en un programa."""
    __tablename__ = "enrollments"
    __table_args__ = {"schema": "academic"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic.programs.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    cohort: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. "2024-1"
    status: Mapped[str] = mapped_column(
        String(50),
        default=StudentStatus.ACTIVE, nullable=False
    )
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_graduation: Mapped[date | None] = mapped_column(Date, nullable=True)
    actual_graduation: Mapped[date | None] = mapped_column(Date, nullable=True)
    gpa: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    ti_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
    program: Mapped["Program"] = relationship("Program", back_populates="enrollments")  # type: ignore
    grades: Mapped[list["SemesterGrade"]] = relationship(
        "SemesterGrade", back_populates="enrollment", lazy="noload"
    )

    @property
    def meets_ti_prerequisite(self) -> bool:
        from app.models.program import Program
        return self.gpa >= 3.5 and self.status == StudentStatus.ACTIVE


class SemesterGrade(Base):
    """Calificación semestral de avance del TI."""
    __tablename__ = "semester_grades"
    __table_args__ = {"schema": "academic"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic.enrollments.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    semester: Mapped[str] = mapped_column(String(20), nullable=False)   # "2024-1"
    grade: Mapped[float] = mapped_column(Float, nullable=False)          # 0.0 - 5.0
    tutor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        default=SemesterGradeStatus.DRAFT, nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="grades")
