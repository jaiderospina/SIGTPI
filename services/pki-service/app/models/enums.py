from enum import StrEnum

class CertificateStatus(StrEnum):
    ACTIVE  = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"

class SignatureStatus(StrEnum):
    VALID   = "valid"
    INVALID = "invalid"
