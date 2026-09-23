from enum import StrEnum

class NotificationChannel(StrEnum):
    EMAIL    = "email"
    PLATFORM = "platform"
    BOTH     = "both"

class NotificationStatus(StrEnum):
    PENDING   = "pending"
    SENT      = "sent"
    FAILED    = "failed"
    READ      = "read"

class NotificationPriority(StrEnum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"
    URGENT = "urgent"
