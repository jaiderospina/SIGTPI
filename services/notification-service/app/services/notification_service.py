import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.notification import Notification
from app.models.enums import NotificationStatus, NotificationChannel
from app.schemas.notification import NotificationCreateRequest
from app.core.config import settings
from sigtpi_common.utils.logging import get_logger
from sigtpi_common.utils.exceptions import NotFoundError

logger = get_logger(__name__)


async def create_notification(db: AsyncSession, data: NotificationCreateRequest) -> Notification:
    notif = Notification(**data.model_dump())
    db.add(notif)
    await db.flush()
    # Try to send immediately for high priority
    if data.channel in [NotificationChannel.EMAIL, NotificationChannel.BOTH]:
        await _try_send_email(db, notif)
    return notif


async def _try_send_email(db: AsyncSession, notif: Notification) -> None:
    if not notif.recipient_email:
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = notif.subject
        msg["From"] = settings.smtp_from
        msg["To"] = notif.recipient_email
        msg.attach(MIMEText(notif.body, "plain"))
        if notif.html_body:
            msg.attach(MIMEText(notif.html_body, "html"))
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
            server.sendmail(settings.smtp_from, [notif.recipient_email], msg.as_string())
        notif.status = NotificationStatus.SENT.value
        notif.sent_at = datetime.now(timezone.utc)
        logger.info("email_sent", to=notif.recipient_email, subject=notif.subject)
    except Exception as e:
        notif.status = NotificationStatus.FAILED.value
        notif.error_message = str(e)
        logger.warning("email_failed", to=notif.recipient_email, error=str(e))
    await db.flush()


async def list_notifications(
    db: AsyncSession, recipient_id: UUID,
    unread_only: bool = False, page: int = 1, page_size: int = 20,
) -> tuple[int, list[Notification]]:
    q = select(Notification).where(Notification.recipient_id == recipient_id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    q = q.order_by(Notification.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    items = (await db.execute(q.offset((page-1)*page_size).limit(page_size))).scalars().all()
    return total, list(items)


async def mark_read(db: AsyncSession, notif_id: UUID, user_id: UUID) -> Notification:
    r = await db.execute(select(Notification).where(Notification.id == notif_id))
    notif = r.scalar_one_or_none()
    if not notif:
        raise NotFoundError("Notificación", notif_id)
    notif.is_read = True
    notif.status = NotificationStatus.READ.value
    notif.read_at = datetime.now(timezone.utc)
    await db.flush()
    return notif


async def get_unread_count(db: AsyncSession, user_id: UUID) -> dict:
    total = (await db.execute(
        select(func.count()).where(
            and_(Notification.recipient_id == user_id, Notification.is_read == False)
        )
    )).scalar_one()
    urgent = (await db.execute(
        select(func.count()).where(
            and_(Notification.recipient_id == user_id,
                 Notification.is_read == False, Notification.priority == "urgent")
        )
    )).scalar_one()
    return {"user_id": user_id, "unread_count": total, "urgent_count": urgent}
