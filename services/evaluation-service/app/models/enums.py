from enum import StrEnum

class EvaluationType(StrEnum):
    ANTEPROJECT  = "anteproject"
    SEMESTER     = "semester_advance"
    PRELIMINARY  = "preliminary_defense"
    FINAL        = "final_defense"

class Dictamen(StrEnum):
    APPROVED              = "approved"
    APPROVED_WITH_CHANGES = "approved_with_changes"
    REJECTED              = "rejected"
    PENDING               = "pending"

class EvaluationStatus(StrEnum):
    DRAFT     = "draft"
    SUBMITTED = "submitted"
    PUBLISHED = "published"
