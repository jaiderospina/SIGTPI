from fastapi import APIRouter
from app.api.v1.endpoints import health, sessions

router = APIRouter()
router.include_router(health.router,   prefix="/health-detail", tags=["Health"])
router.include_router(sessions.router, prefix="/sessions",      tags=["Sesiones y Actas"])
