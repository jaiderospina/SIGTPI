"""Modelo ORM Usuario para user-service."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sigtpi_common.utils.database import Base
from app.models.enums import UserStatus


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "users"}

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    document_id: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    area_of_expertise: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        default=UserStatus.ACTIVE, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    roles: Mapped[list["UserRole"]] = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin"
    )
    program_memberships: Mapped[list["ProgramMembership"]] = relationship(
        "ProgramMembership", back_populates="user", cascade="all, delete-orphan", lazy="noload"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"

    @property
    def role_codes(self) -> list[str]:
        return [ur.role_code for ur in self.roles if ur.is_active]
