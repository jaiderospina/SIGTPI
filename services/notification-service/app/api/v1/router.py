from fastapi import APIRouter
from app.api.v1.endpoints import health, notifications

router = APIRouter()
router.include_router(health.router,        prefix="/health-detail",  tags=["Health"])
router.include_router(notifications.router, prefix="/notifications",   tags=["Notificaciones"])
