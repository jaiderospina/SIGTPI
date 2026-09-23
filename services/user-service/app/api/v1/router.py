"""API v1 router para user-service."""
from fastapi import APIRouter
from app.api.v1.endpoints import health, users, roles

router = APIRouter()
router.include_router(health.router,  prefix="/health-detail", tags=["Health"])
router.include_router(users.router,   prefix="/users",         tags=["Usuarios"])
router.include_router(roles.router,   prefix="/roles",         tags=["Roles RBAC"])
