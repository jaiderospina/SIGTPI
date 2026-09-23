"""Pydantic schemas for user-service."""
from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import RoleCode, UserStatus


# ── Role schemas ──────────────────────────────────────────────────────────────
class RoleRead(BaseSchema):
    id: UUID
    role_code: str
    program_id: UUID | None = None
    is_active: bool
    assigned_at: datetime
    expires_at: datetime | None = None


class RoleAssignRequest(BaseSchema):
    user_id: UUID
    role_code: RoleCode
    program_id: UUID | None = None
    expires_at: datetime | None = None


class RoleRevokeRequest(BaseSchema):
    user_id: UUID
    role_code: RoleCode
    program_id: UUID | None = None


# ── Program membership schemas ────────────────────────────────────────────────
class ProgramMembershipRead(BaseSchema):
    id: UUID
    program_id: UUID
    program_name: str
    is_active: bool
    joined_at: datetime


# ── User schemas ──────────────────────────────────────────────────────────────
class UserCreateRequest(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=255)
    document_id: str | None = Field(None, max_length=50)
    phone: str | None = Field(None, max_length=20)
    area_of_expertise: str | None = Field(None, max_length=255)
    initial_role: RoleCode = RoleCode.EST
    program_id: UUID | None = None


class UserUpdateRequest(BaseSchema):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    bio: str | None = None
    area_of_expertise: str | None = Field(None, max_length=255)
    photo_url: str | None = None


class UserStatusUpdateRequest(BaseSchema):
    status: UserStatus
    reason: str | None = None


class UserRead(IdentifiedSchema):
    email: str
    full_name: str
    document_id: str | None = None
    phone: str | None = None
    photo_url: str | None = None
    bio: str | None = None
    area_of_expertise: str | None = None
    status: str
    is_superuser: bool
    roles: list[RoleRead] = []

    @property
    def role_codes(self) -> list[str]:
        return [r.role_code for r in self.roles if r.is_active]


class UserSummary(BaseSchema):
    """Vista reducida de usuario para listados."""
    id: UUID
    email: str
    full_name: str
    status: str
    role_codes: list[str]
    area_of_expertise: str | None = None


class UserListResponse(BaseSchema):
    total: int
    page: int
    page_size: int
    items: list[UserSummary]


class RBACCheckRequest(BaseSchema):
    user_id: UUID
    required_roles: list[str]
    program_id: UUID | None = None


class RBACCheckResponse(BaseSchema):
    user_id: UUID
    has_permission: bool
    effective_roles: list[str]
