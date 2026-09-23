from uuid import UUID
from datetime import datetime
from pydantic import EmailStr, Field
from sigtpi_common.schemas.base import BaseSchema, IdentifiedSchema
from app.models.enums import NotificationChannel, NotificationPriority, NotificationStatus


class NotificationCreateRequest(BaseSchema):
    recipient_id: UUID
    recipient_email: str | None = None
    subject: str = Field(..., min_length=3, max_length=255)
    body: str = Field(..., min_length=1)
    html_body: str | None = None
    channel: NotificationChannel = NotificationChannel.BOTH
    priority: NotificationPriority = NotificationPriority.MEDIUM
    event_type: str | None = None
    reference_id: UUID | None = None
    extra_data: dict | None = None


class NotificationRead(IdentifiedSchema):
    recipient_id: UUID
    subject: str
    body: str
    channel: str
    priority: str
    status: str
    event_type: str | None
    is_read: bool
    sent_at: datetime | None
    read_at: datetime | None
    created_at: datetime


class NotificationSummary(BaseSchema):
    id: UUID
    subject: str
    priority: str
    status: str
    is_read: bool
    event_type: str | None
    created_at: datetime


class UnreadCountResponse(BaseSchema):
    user_id: UUID
    unread_count: int
    urgent_count: int
