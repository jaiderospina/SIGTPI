from fastapi import APIRouter
from app.api.v1.endpoints import health, certificates

router = APIRouter()
router.include_router(health.router,      prefix="/health-detail", tags=["Health"])
router.include_router(certificates.router, prefix="/pki",          tags=["PKI — Certificados y Firmas"])
