"""Pydantic schemas for auth-service."""
from uuid import UUID
from pydantic import EmailStr, Field, field_validator
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=1)
    totp_code: str | None = Field(None, description="6-digit TOTP code if MFA is enabled")


class TokenResponse(BaseSchema):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    requires_totp: bool = False


class TOTPSetupRequest(BaseSchema):
    password: str = Field(..., description="Current password to confirm identity")


class TOTPSetupResponse(BaseSchema):
    secret: str
    qr_uri: str
    backup_codes: list[str] = []
    qr_uri: str
    backup_codes: list[str]


class TOTPVerifyRequest(BaseSchema):
    totp_code: str = Field(..., min_length=6, max_length=6)


class PasswordChangeRequest(BaseSchema):
    current_password: str
    new_password: str = Field(..., min_length=10)

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character.")
        return v


class UserCreateRequest(BaseSchema):
    email: EmailStr
    password: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=2, max_length=255)


class UserResponse(IdentifiedSchema):
    email: str
    full_name: str
    is_active: bool
    totp_enabled: bool
