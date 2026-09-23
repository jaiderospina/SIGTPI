from enum import StrEnum
from datetime import datetime, timezone
from uuid import uuid4, UUID
from pydantic import BaseModel, Field

class EventType(StrEnum):
    USER_LOGGED_IN = "auth.user.logged_in"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ROLE_ASSIGNED = "user.role.assigned"
    TUTOR_ASSIGNED = "tutoring.tutor.assigned"
    TUTOR_ASSIGNMENT_ACCEPTED = "tutoring.assignment.accepted"
    TUTOR_ASSIGNMENT_REJECTED = "tutoring.assignment.rejected"
    COMMITTEE_FORMED = "tutoring.committee.formed"
    TI_REGISTERED = "ti.registered"
    TI_ANTEPROJECT_SUBMITTED = "ti.anteproject.submitted"
    TI_ANTEPROJECT_APPROVED = "ti.anteproject.approved"
    TI_MILESTONE_COMPLETED = "ti.milestone.completed"
    TI_DELAY_ALERT = "ti.delay.alert"
    TI_DELIVERABLE_UPLOADED = "ti.deliverable.uploaded"
    TI_FEEDBACK_REGISTERED = "ti.feedback.registered"
    SESSION_SCHEDULED = "session.scheduled"
    SESSION_COMPLETED = "session.completed"
    SESSION_CANCELLED = "session.cancelled"
    SESSION_MINUTES_SIGNED = "session.minutes.signed"
    EVALUATION_SUBMITTED = "evaluation.submitted"
    DICTAMEN_ISSUED = "evaluation.dictamen.issued"
    DOCUMENT_UPLOADED = "document.uploaded"
    SIMILARITY_REPORT_READY = "document.similarity.ready"
    NOTIFICATION_REQUESTED = "notification.requested"

class DomainEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: UUID
    aggregate_type: str
    payload: dict
    source_service: str
    correlation_id: UUID | None = None
