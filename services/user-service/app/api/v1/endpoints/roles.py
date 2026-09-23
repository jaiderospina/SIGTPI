"""Endpoints de gestión de roles RBAC."""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.user import (
    RoleAssignRequest, RoleRevokeRequest, RoleRead,
    RBACCheckRequest, RBACCheckResponse,
)
from app.services import user_service
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError

router = APIRouter()


@router.post("/assign", response_model=RoleRead, status_code=status.HTTP_201_CREATED,
             summary="Asignar rol a usuario")
async def assign_role(
    data: RoleAssignRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        role = await user_service.assign_role(db, data, UUID(current_user.sub))
        return RoleRead(
            id=role.id, role_code=role.role_code, program_id=role.program_id,
            is_active=role.is_active, assigned_at=role.assigned_at, expires_at=role.expires_at,
        )
    except (NotFoundError, ConflictError) as e:
        code = 404 if isinstance(e, NotFoundError) else 409
        raise HTTPException(status_code=code, detail=e.message)


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT, summary="Revocar rol de usuario")
async def revoke_role(
    data: RoleRevokeRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR")),
    db: AsyncSession = Depends(get_db),
):
    try:
        await user_service.revoke_role(db, data, UUID(current_user.sub))
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check", response_model=RBACCheckResponse, summary="Verificar permisos RBAC")
async def check_rbac(
    data: RBACCheckRequest,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Endpoint interno usado por otros microservicios para verificar permisos."""
    has_permission, effective_roles = await user_service.check_rbac(
        db, data.user_id, data.required_roles, data.program_id
    )
    return RBACCheckResponse(
        user_id=data.user_id,
        has_permission=has_permission,
        effective_roles=effective_roles,
    )


@router.get("/user/{user_id}", summary="Obtener roles activos de un usuario")
async def get_user_roles(
    user_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM", "COO", "DIR")),
    db: AsyncSession = Depends(get_db),
):
    user = await user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario {user_id} no encontrado.")
    return {
        "user_id": user_id,
        "roles": [
            RoleRead(
                id=r.id, role_code=r.role_code, program_id=r.program_id,
                is_active=r.is_active, assigned_at=r.assigned_at, expires_at=r.expires_at,
            )
            for r in user.roles
        ],
        "effective_role_codes": user.role_codes,
    }
