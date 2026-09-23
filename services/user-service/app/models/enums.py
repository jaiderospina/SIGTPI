"""Enumeraciones compartidas del dominio SIGTPI."""
from enum import StrEnum


class RoleCode(StrEnum):
    EST = "EST"   # Estudiante de Postgrado
    TUT = "TUT"   # Tutor Principal
    COT = "COT"   # Co-Tutor
    CEV = "CEV"   # Comité Evaluador
    DIR = "DIR"   # Director de Programa
    COO = "COO"   # Coordinador Académico
    ADM = "ADM"   # Administrador del Sistema
    EXT = "EXT"   # Evaluador Externo


class UserStatus(StrEnum):
    ACTIVE   = "active"
    INACTIVE = "inactive"
    LOCKED   = "locked"
    PENDING  = "pending"


# Role hierarchy: roles que heredan permisos de otros
ROLE_HIERARCHY: dict[RoleCode, list[RoleCode]] = {
    RoleCode.ADM: [RoleCode.ADM, RoleCode.DIR, RoleCode.COO, RoleCode.TUT,
                   RoleCode.COT, RoleCode.CEV, RoleCode.EST, RoleCode.EXT],
    RoleCode.DIR: [RoleCode.DIR, RoleCode.COO, RoleCode.TUT, RoleCode.COT,
                   RoleCode.CEV, RoleCode.EST, RoleCode.EXT],
    RoleCode.COO: [RoleCode.COO, RoleCode.TUT, RoleCode.COT, RoleCode.CEV, RoleCode.EXT],
    RoleCode.TUT: [RoleCode.TUT, RoleCode.COT],
    RoleCode.COT: [RoleCode.COT],
    RoleCode.CEV: [RoleCode.CEV],
    RoleCode.EST: [RoleCode.EST],
    RoleCode.EXT: [RoleCode.EXT],
}


def get_effective_roles(role: RoleCode) -> list[str]:
    """Retorna todos los roles efectivos de un rol dado (con herencia)."""
    return [r.value for r in ROLE_HIERARCHY.get(role, [role])]
