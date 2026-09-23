from enum import StrEnum

class SessionModality(StrEnum):
    PRESENTIAL = "presential"
    VIRTUAL    = "virtual"
    HYBRID     = "hybrid"

class SessionStatus(StrEnum):
    SCHEDULED    = "scheduled"
    CONFIRMED    = "confirmed"
    IN_PROGRESS  = "in_progress"
    COMPLETED    = "completed"
    CANCELLED    = "cancelled"
    RESCHEDULED  = "rescheduled"

class MinutesStatus(StrEnum):
    DRAFT     = "draft"
    PENDING   = "pending"    # waiting student confirmation
    CONFIRMED = "confirmed"  # student confirmed
    DISPUTED  = "disputed"   # student raised objection
    CLOSED    = "closed"     # closed unilaterally by tutor
