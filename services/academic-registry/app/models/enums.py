from enum import StrEnum

class ProgramLevel(StrEnum):
    MAESTRIA  = "maestria"
    DOCTORADO = "doctorado"

class ProgramStatus(StrEnum):
    ACTIVE   = "active"
    INACTIVE = "inactive"

class StudentStatus(StrEnum):
    ACTIVE    = "active"
    PAUSED    = "paused"
    GRADUATED = "graduated"
    WITHDRAWN = "withdrawn"

class SemesterGradeStatus(StrEnum):
    DRAFT     = "draft"
    SUBMITTED = "submitted"
    APPROVED  = "approved"
