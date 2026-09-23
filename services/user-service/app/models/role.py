"""Modelos ORM para roles y permisos."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base


class UserRole(Base):
    """Asignación de rol a un usuario."""
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_code", name="uq_user_role"),
        {"schema": "users"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_code: Mapped[str] = mapped_column(String(10), nullable=False)
    program_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="roles")  # type: ignore

    def __repr__(self) -> str:
        return f"<UserRole user={self.user_id} role={self.role_code}>"


class ProgramMembership(Base):
    """Pertenencia de un usuario a un programa académico."""
    __tablename__ = "program_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "program_id", name="uq_user_program"),
        {"schema": "users"},
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    program_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    program_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="program_memberships")  # type: ignore
