"""Core authentication business logic."""
from datetime import datetime, timezone
import pyotp
import secrets
import string
from uuid import UUID
import bcrypt as _bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreateRequest
from app.core.config import settings
from sigtpi_common.security.jwt import create_access_token
from sigtpi_common.utils.exceptions import UnauthorizedError, ConflictError, NotFoundError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, data: UserCreateRequest) -> User:
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ConflictError(f"Email '{data.email}' is already registered.")
    user = User(
        email=data.email.lower(),
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
    )
    db.add(user)
    await db.flush()
    logger.info("user_created", user_id=str(user.id), email=user.email)
    return user


async def authenticate(db: AsyncSession, req: LoginRequest) -> tuple[User, bool]:
    """
    Returns (user, needs_totp).
    Raises UnauthorizedError on bad credentials or locked account.
    """
    user = await get_user_by_email(db, req.email)
    if not user or not user.is_active:
        raise UnauthorizedError("Invalid credentials.")

    # Check lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise UnauthorizedError(
            f"Account locked until {user.locked_until.isoformat()}. Too many failed attempts.")

    if not verify_password(req.password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            from datetime import timedelta
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_MINUTES)
            logger.warning("account_locked", user_id=str(user.id), email=user.email)
        await db.flush()
        raise UnauthorizedError("Invalid credentials.")

    # Reset failed attempts on successful password check
    user.failed_login_attempts = 0
    user.locked_until = None

    needs_totp = user.totp_enabled and req.totp_code is None
    if user.totp_enabled and req.totp_code is not None:
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(req.totp_code, valid_window=1):
            raise UnauthorizedError("Invalid TOTP code.")

    user.last_login = datetime.now(timezone.utc)
    await db.flush()
    return user, needs_totp


def issue_token(user: User, roles: list[str]) -> TokenResponse:
    token = create_access_token(
        subject=user.id,
        roles=roles,
        secret_key=settings.jwt_secret_key,
        expires_minutes=settings.jwt_access_token_expire_minutes,
        algorithm=settings.jwt_algorithm,
    )
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


def generate_totp_setup(user: User) -> dict:
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.email, issuer_name="SIGTPI")
    backup_codes = [
        "".join(secrets.choice(string.digits) for _ in range(8))
        for _ in range(8)
    ]
    return {"secret": secret, "qr_uri": uri, "backup_codes": backup_codes}
