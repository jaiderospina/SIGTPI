"""FastAPI dependency injection para user-service."""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.config import settings
from app.core.database import get_db
from sigtpi_common.security.jwt import decode_token, TokenPayload

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> TokenPayload:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación requerido.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(
            credentials.credentials,
            settings.jwt_secret_key,
            settings.jwt_algorithm
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


def require_roles(*roles: str):
    """Factory para control de acceso basado en roles."""
    async def _check(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if not any(r in current_user.roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Se requiere uno de los roles: {', '.join(roles)}",
            )
        return current_user
    return _check
