"""Lógica de negocio del directorio de usuarios y RBAC."""
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import UserRole, ProgramMembership
from app.models.enums import RoleCode, UserStatus, ROLE_HIERARCHY, get_effective_roles
from app.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserStatusUpdateRequest,
    RoleAssignRequest, RoleRevokeRequest,
)
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError
from sigtpi_common.utils.logging import get_logger

logger = get_logger(__name__)


# ── Queries ───────────────────────────────────────────────────────────────────
async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def list_users(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    role_code: str | None = None,
    status: str | None = None,
    search: str | None = None,
    program_id: UUID | None = None,
) -> tuple[int, list[User]]:
    q = select(User).options(selectinload(User.roles))

    if status:
        q = q.where(User.status == status)
    if search:
        term = f"%{search}%"
        q = q.where(or_(User.full_name.ilike(term), User.email.ilike(term)))
    if role_code:
        q = q.join(UserRole).where(UserRole.role_code == role_code, UserRole.is_active == True)
    if program_id:
        q = q.join(ProgramMembership).where(
            ProgramMembership.program_id == program_id, ProgramMembership.is_active == True
        )

    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar_one()
    items = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return total, list(items)


# ── Commands ──────────────────────────────────────────────────────────────────
async def create_user(
    db: AsyncSession,
    data: UserCreateRequest,
    created_by: UUID | None = None,
) -> User:
    """Create user in both auth table (public.users) and profile table (users.users)."""
    from sqlalchemy import text
    import secrets, uuid as _uuid
    from sigtpi_common.security.password import hash_password

    # Check profile table
    existing = await get_user_by_email(db, data.email)
    if existing:
        raise ConflictError(f"El email '{data.email}' ya está registrado.")

    # Check auth table (explicit schema to avoid search_path ambiguity)
    auth_check = await db.execute(
        text("SELECT id FROM public.users WHERE email = :email"),
        {"email": data.email.lower()}
    )
    if auth_check.fetchone():
        raise ConflictError(f"El email '{data.email}' ya está registrado.")

    temp_password = secrets.token_urlsafe(12)
    hashed_pw = hash_password(temp_password)
    new_id = _uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 1. Auth record — enables login via auth-service
    await db.execute(text("""
        INSERT INTO public.users
            (id, email, hashed_password, full_name, is_active, is_superuser,
             totp_enabled, failed_login_attempts, created_at, updated_at)
        VALUES
            (:id, :email, :pw, :name, true, false, false, 0, :now, :now)
    """), {
        "id": str(new_id),
        "email": data.email.lower(),
        "pw": hashed_pw,
        "name": data.full_name,
        "now": now,
    })

    # 2. Profile record — user-service directory
    user = User(
        id=new_id,
        email=data.email.lower(),
        full_name=data.full_name,
        document_id=data.document_id,
        phone=data.phone,
        area_of_expertise=data.area_of_expertise,
        status=UserStatus.ACTIVE.value,
    )
    db.add(user)
    await db.flush()

    # 3. Role assignment — enables correct JWT at login
    role = UserRole(
        user_id=user.id,
        role_code=data.initial_role.value,
        program_id=data.program_id,
        assigned_by=created_by,
    )
    db.add(role)

    if data.program_id:
        db.add(ProgramMembership(
            user_id=user.id,
            program_id=data.program_id,
            program_name="",
        ))

    await db.flush()
    logger.info("user_created",
                user_id=str(user.id), email=user.email,
                role=data.initial_role.value,
                temp_password=temp_password)  # visible in service logs / MailHog
    return user


async def update_user(db: AsyncSession, user_id: UUID, data: UserUpdateRequest) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("Usuario", user_id)

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return user


async def update_user_status(
    db: AsyncSession, user_id: UUID, data: UserStatusUpdateRequest, updated_by: UUID
) -> User:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise NotFoundError("Usuario", user_id)
    if user.is_superuser and data.status == UserStatus.INACTIVE:
        raise ForbiddenError("No se puede desactivar un superusuario.")
    user.status = data.status
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("user_status_updated", user_id=str(user_id), status=data.status, by=str(updated_by))
    return user


# ── RBAC ─────────────────────────────────────────────────────────────────────
async def assign_role(
    db: AsyncSession, data: RoleAssignRequest, assigned_by: UUID
) -> UserRole:
    user = await get_user_by_id(db, data.user_id)
    if not user:
        raise NotFoundError("Usuario", data.user_id)

    # Check if role already active
    existing = next(
        (r for r in user.roles
         if r.role_code == data.role_code.value
         and r.program_id == data.program_id
         and r.is_active),
        None,
    )
    if existing:
        raise ConflictError(f"El usuario ya tiene el rol '{data.role_code}' activo.")

    role = UserRole(
        user_id=data.user_id,
        role_code=data.role_code.value,
        program_id=data.program_id,
        assigned_by=assigned_by,
        expires_at=data.expires_at,
    )
    db.add(role)
    await db.flush()
    logger.info("role_assigned", user_id=str(data.user_id), role=data.role_code, by=str(assigned_by))
    return role


async def revoke_role(db: AsyncSession, data: RoleRevokeRequest, revoked_by: UUID) -> None:
    user = await get_user_by_id(db, data.user_id)
    if not user:
        raise NotFoundError("Usuario", data.user_id)

    role = next(
        (r for r in user.roles
         if r.role_code == data.role_code.value
         and r.program_id == data.program_id
         and r.is_active),
        None,
    )
    if not role:
        raise NotFoundError("Rol activo", f"{data.role_code} para usuario {data.user_id}")

    role.is_active = False
    await db.flush()
    logger.info("role_revoked", user_id=str(data.user_id), role=data.role_code, by=str(revoked_by))


async def check_rbac(
    db: AsyncSession, user_id: UUID, required_roles: list[str], program_id: UUID | None = None
) -> tuple[bool, list[str]]:
    """Verifica si un usuario tiene al menos uno de los roles requeridos."""
    user = await get_user_by_id(db, user_id)
    if not user or user.status != UserStatus.ACTIVE:
        return False, []

    effective: set[str] = set()
    for ur in user.roles:
        if not ur.is_active:
            continue
        if program_id and ur.program_id and ur.program_id != program_id:
            continue
        try:
            role = RoleCode(ur.role_code)
            effective.update(get_effective_roles(role))
        except ValueError:
            effective.add(ur.role_code)

    has_permission = bool(effective.intersection(required_roles))
    return has_permission, sorted(effective)
