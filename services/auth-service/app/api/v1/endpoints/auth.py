"""Authentication endpoints: login, logout, MFA setup, token refresh."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.auth import (
    LoginRequest, TokenResponse, TOTPSetupResponse,
    TOTPSetupRequest, TOTPVerifyRequest, UserCreateRequest, UserResponse,
    PasswordChangeRequest,
)
from app.services.auth_service import (
    authenticate, create_user, issue_token, generate_totp_setup,
    verify_password, hash_password, get_user_by_id,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import (
    UnauthorizedError, ConflictError, NotFoundError
)
from sigtpi_common.utils.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)



async def _get_user_roles(db, user_id: str, is_superuser: bool) -> list[str]:
    """Fetch roles from user_roles table (search_path includes users schema).
    Falls back to is_superuser flag if query fails or returns nothing."""
    try:
        from sqlalchemy import text
        # search_path is set to public,users in the DB connection URL
        # so we can use just 'user_roles' without schema prefix
        result = await db.execute(
            text("SELECT role_code FROM user_roles WHERE user_id = :uid AND is_active = true"),
            {"uid": user_id}
        )
        roles = [row[0] for row in result.fetchall()]
        if roles:
            return roles
    except Exception as e:
        pass
    # Fallback
    return ["ADM"] if is_superuser else ["EST"]

@router.post("/login", response_model=TokenResponse, summary="Login with email + password (+ TOTP if enabled)")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user, needs_totp = await authenticate(db, req)
    except UnauthorizedError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=e.message)

    if needs_totp:
        return TokenResponse(
            access_token="",
            expires_in=0,
            requires_totp=True,
        )

    # For now, superusers get ["ADM"], others get ["EST"]
    roles = ["ADM"] if user.is_superuser else ["EST"]
    token_response = issue_token(user, roles)
    logger.info("user_logged_in", user_id=str(user.id))
    return token_response


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED,
             summary="Register a new user (admin or self-registration if enabled)")
async def register(req: UserCreateRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = await create_user(db, req)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    return UserResponse(
        id=user.id, email=user.email, full_name=user.full_name,
        is_active=user.is_active, totp_enabled=user.totp_enabled,
        created_at=user.created_at, updated_at=user.updated_at,
    )


@router.post("/mfa/setup", response_model=TOTPSetupResponse, summary="Initiate TOTP MFA setup")
async def setup_mfa(
    req: TOTPSetupRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    user = await get_user_by_id(db, UUID(current_user.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    setup = generate_totp_setup(user)
    # Store secret temporarily — user must verify before we activate
    user.totp_secret = setup["secret"]
    await db.flush()
    return TOTPSetupResponse(**setup)


@router.post("/mfa/verify", summary="Confirm TOTP code and activate MFA")
async def verify_mfa(
    req: TOTPVerifyRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    import pyotp
    user = await get_user_by_id(db, UUID(current_user.sub))
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="MFA setup not initiated.")
    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(req.totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code.")
    user.totp_enabled = True
    await db.flush()
    logger.info("mfa_activated", user_id=str(user.id))
    return {"message": "MFA activated successfully."}


@router.post("/mfa/disable", summary="Disable TOTP MFA")
async def disable_mfa(
    req: TOTPSetupRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    user = await get_user_by_id(db, UUID(current_user.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password.")
    user.totp_enabled = False
    user.totp_secret = None
    await db.flush()
    return {"message": "MFA disabled."}


@router.post("/password/change", summary="Change current user password")
async def change_password(
    req: PasswordChangeRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    user = await get_user_by_id(db, UUID(current_user.sub))
    if not user or not verify_password(req.current_password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect current password.")
    user.hashed_password = hash_password(req.new_password)
    await db.flush()
    return {"message": "Password updated successfully."}


@router.get("/me", summary="Get current user info")
async def me(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    user = await get_user_by_id(db, UUID(current_user.sub))
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    # Build roles from token payload (set at login time)
    roles = [
        {"id": str(UUID(int=i)), "role_code": r, "is_active": True,
         "program_id": None, "assigned_at": user.created_at.isoformat(),
         "expires_at": None}
        for i, r in enumerate(current_user.roles)
    ]
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "totp_enabled": user.totp_enabled,
        "status": "active",
        "roles": roles,
        "program_memberships": [],
        "created_at": user.created_at.isoformat(),
        "updated_at": user.updated_at.isoformat(),
    }
