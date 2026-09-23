"""API v1 router for auth-service."""
from fastapi import APIRouter
from app.api.v1.endpoints import health, auth

router = APIRouter()
router.include_router(health.router, prefix="/health-detail", tags=["Health Detail"])
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
