from enum import StrEnum

class TIStatus(StrEnum):
    DRAFT            = "draft"
    ANTEPROJECT      = "anteproject"
    IN_PROGRESS      = "in_progress"
    PRELIMINARY_DEF  = "preliminary_defense"
    FINAL_DEF        = "final_defense"
    APPROVED         = "approved"
    WITHDRAWN        = "withdrawn"

class MilestoneType(StrEnum):
    ANTEPROJECT_SUBMISSION  = "anteproject_submission"
    ANTEPROJECT_APPROVAL    = "anteproject_approval"
    SEMESTER_ADVANCE        = "semester_advance"
    PRELIMINARY_DEFENSE     = "preliminary_defense"
    FINAL_DRAFT             = "final_draft"
    FINAL_DEFENSE           = "final_defense"
    CUSTOM                  = "custom"

class MilestoneStatus(StrEnum):
    PENDING   = "pending"
    IN_REVIEW = "in_review"
    APPROVED  = "approved"
    REJECTED  = "rejected"
    OVERDUE   = "overdue"

class AlertLevel(StrEnum):
    L1_INFO     = "1"   # 7 days before deadline — notify student
    L2_WARNING  = "2"   # deadline passed — notify tutor
    L3_RISK     = "3"   # 14 days overdue — notify coordinator
    L4_CRITICAL = "4"   # 30 days overdue — notify director

class AlertStatus(StrEnum):
    ACTIVE     = "active"
    RESOLVED   = "resolved"
    JUSTIFIED  = "justified"
    ESCALATED  = "escalated"

class KnowledgeArea(StrEnum):
    CYBERSECURITY   = "Ciberseguridad y Ciberdefensa"
    NETWORKS        = "Redes y Telecomunicaciones"
    DATA_SCIENCE    = "Ciencia de Datos e IA"
    SOFTWARE_ENG    = "Ingeniería de Software"
    SYSTEMS_MGMT    = "Gestión de Sistemas de Información"
    OTHER           = "Otra"
