from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.deps import get_current_user, require_roles
from app.schemas.academic import (
    ProgramCreateRequest, ProgramUpdateRequest, ProgramRead, ProgramSummary
)
from app.services.academic_service import (
    list_programs, get_program, create_program, update_program
)
from sigtpi_common.security.jwt import TokenPayload
from sigtpi_common.utils.exceptions import NotFoundError, ConflictError
from sigtpi_common.utils.logging import get_logger

router  = APIRouter()
logger  = get_logger(__name__)


@router.get("", response_model=list[ProgramSummary])
async def list_all(
    status: str | None = Query(None),
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        programs = await list_programs(db, status)
        return [ProgramSummary(
            id=p.id, code=p.code, name=p.name,
            level=str(p.level.value if hasattr(p.level,'value') else p.level),
            status=str(p.status.value if hasattr(p.status,'value') else p.status),
        ) for p in programs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar programas: {e}")


@router.post("", response_model=ProgramRead, status_code=201)
async def create(
    data: ProgramCreateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "DIR", "COO")),
    db: AsyncSession = Depends(get_db),
):
    try:
        prog = await create_program(db, data)
        return ProgramRead.model_validate(prog)
    except ConflictError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except Exception as e:
        logger.error("program_create_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al crear programa: {e}")


@router.get("/{program_id}", response_model=ProgramRead)
async def get_one(
    program_id: UUID,
    current_user: TokenPayload = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    prog = await get_program(db, program_id)
    if not prog:
        raise HTTPException(status_code=404, detail="Programa no encontrado.")
    return ProgramRead.model_validate(prog)


@router.patch("/{program_id}", response_model=ProgramRead)
async def update(
    program_id: UUID,
    data: ProgramUpdateRequest,
    current_user: TokenPayload = Depends(require_roles("ADM", "DIR", "COO")),
    db: AsyncSession = Depends(get_db),
):
    try:
        prog = await update_program(db, program_id, data)
        return ProgramRead.model_validate(prog)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except Exception as e:
        logger.error("program_update_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error al actualizar: {e}")


@router.delete("/{program_id}", status_code=204)
async def delete(
    program_id: UUID,
    current_user: TokenPayload = Depends(require_roles("ADM")),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import text
    await db.execute(
        text("UPDATE academic.programs SET status='inactive' WHERE id=:id"),
        {"id": str(program_id)}
    )
    await db.commit()
