"""Endpoints CRUD de usuarios."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.user import (
    UserCreateRequest, UserUpdateRequest, UserStatusUpdateRequest,
    UserRead, UserSummary, UserListResponse,
)
from app.services import user_service
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError, ForbiddenError

router = APIRouter()


@router.get("", response_model=UserListResponse, summary="Listar usuarios con filtros")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_code: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    program_id: UUID | None = Query(None),
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        total, users = await user_service.list_users(
            db, page, page_size, role_code, status, search, program_id
        )
        items = [
            UserSummary(
                id=u.id, email=u.email, full_name=u.full_name,
                status=str(u.status.value if hasattr(u.status,'value') else u.status),
                role_codes=u.role_codes,
                area_of_expertise=u.area_of_expertise,
            )
            for u in users
        ]
        return UserListResponse(total=total, page=page, page_size=page_size, items=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar usuarios: {e}")


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED,
             summary="Crear usuario en el directorio")
async def create_user(
    data: UserCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO")),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_service.create_user(db, data, created_by=UUID(current_user.sub))
        return UserRead.model_validate(user)
    except ConflictError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
    except Exception as e:
        from sigtpi_common.utils.logging import get_logger
        get_logger(__name__).error("user_create_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al crear usuario: {e}")


@router.get("/me", response_model=UserRead, summary="Perfil del usuario autenticado")
async def get_my_profile(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, UUID(current_user.sub))
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead, summary="Obtener usuario por ID")
async def get_user(
    user_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR", "TUT")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado.")
    return UserRead.model_validate(user)


@router.patch("/{user_id}", response_model=UserRead, summary="Actualizar perfil de usuario")
async def update_user(
    user_id: UUID,
    data: UserUpdateRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Users can update their own profile; ADM/COO can update any
    if str(user_id) != current_user.sub and not any(r in current_user.roles for r in ["ADM", "COO"]):
        raise HTTPException(status_code=403, detail="Solo puedes editar tu propio perfil.")
    try:
        user = await user_service.update_user(db, user_id, data)
        return UserRead.model_validate(user)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.patch("/{user_id}/status", response_model=UserRead, summary="Cambiar estado de usuario")
async def update_status(
    user_id: UUID,
    data: UserStatusUpdateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM")),
    db: AsyncSession = Depends(get_db),
):
    try:
        user = await user_service.update_user_status(db, user_id, data, UUID(current_user.sub))
        return UserRead.model_validate(user)
    except (NotFoundError, ForbiddenError) as e:
        code = 404 if isinstance(e, NotFoundError) else 403
        raise HTTPException(status_code=code, detail=e.message)
