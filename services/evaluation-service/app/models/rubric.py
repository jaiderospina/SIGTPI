import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base


class Rubric(Base):
    """Rúbrica de evaluación configurable por programa."""
    __tablename__ = "rubrics"
    __table_args__ = {"schema": "evaluation"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    program_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    evaluation_type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    criteria: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # criteria: [{"id":"c1","name":"Pertinencia","weight":0.25,"descriptors":{"5":"...","4":"..."}}]
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    evaluations: Mapped[list["Evaluation"]] = relationship(
        "Evaluation", back_populates="rubric", lazy="noload"
    )
