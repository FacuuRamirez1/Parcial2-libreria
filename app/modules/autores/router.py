"""Rutas HTTP del módulo autores."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.autores.service import (
    actualizar_autor,
    crear_autor,
    listar_autores,
    obtener_autor,
)

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor_endpoint(data: AutorCreate, session: SessionDep) -> AutorRead:
    return await crear_autor(session, data)


@router.get("/", response_model=PaginatedResponse[AutorRead])
async def listar_autores_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[AutorRead]:
    page, size = pag
    return await listar_autores(
        session,
        offset=(page - 1) * size,
        limit=size,
        page=page,
        size=size,
    )


@router.get("/{id}", response_model=AutorRead)
async def obtener_autor_endpoint(id: int, session: SessionDep) -> AutorRead:
    return await obtener_autor(session, id)


@router.patch("/{id}", response_model=AutorRead)
async def actualizar_autor_endpoint(
    id: int, data: AutorUpdate, session: SessionDep
) -> AutorRead:
    return await actualizar_autor(session, id, data)
