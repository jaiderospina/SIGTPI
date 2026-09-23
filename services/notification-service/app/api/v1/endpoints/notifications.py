from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.notification import (
    NotificationCreateRequest, NotificationRead,
    NotificationSummary, UnreadCountResponse,
)
from app.services.notification_service import (
    create_notification, list_notifications, mark_read, get_unread_count,
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError

router = APIRouter()


@router.post("", response_model=NotificationRead, status_code=201, summary="Crear y enviar notificación")
async def create(
    data: NotificationCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM","COO","DIR","TUT")),
    db: AsyncSession = Depends(get_db),
):
    n = await create_notification(db, data)
    return NotificationRead.model_validate(n)


@router.get("/my", summary="Mis notificaciones")
async def my_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    total, items = await list_notifications(
        db, UUID(current_user.sub), unread_only, page, page_size
    )
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [NotificationSummary.model_validate(n) for n in items]
    }


@router.get("/my/unread-count", response_model=UnreadCountResponse, summary="Contador de no leídas")
async def unread_count(
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return UnreadCountResponse(**(await get_unread_count(db, UUID(current_user.sub))))


@router.post("/{notif_id}/read", response_model=NotificationRead, summary="Marcar como leída")
async def mark_as_read(
    notif_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        n = await mark_read(db, notif_id, UUID(current_user.sub))
        return NotificationRead.model_validate(n)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
