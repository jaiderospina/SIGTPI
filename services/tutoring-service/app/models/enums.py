from enum import StrEnum

class AssignmentStatus(StrEnum):
    PENDING  = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    ACTIVE   = "active"
    CLOSED   = "closed"

class CommitteeRole(StrEnum):
    PRESIDENT = "president"
    MEMBER    = "member"
    EXTERNAL  = "external"

class CommitteeStatus(StrEnum):
    FORMING  = "forming"
    ACTIVE   = "active"
    DISSOLVED= "dissolved"
