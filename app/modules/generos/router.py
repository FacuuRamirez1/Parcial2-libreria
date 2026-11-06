"""Rutas HTTP del módulo generos."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.generos.service import (
    actualizar_genero,
    crear_genero,
    listar_generos,
    obtener_genero,
)

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero_endpoint(data: GeneroCreate, session: SessionDep) -> GeneroRead:
    return await crear_genero(session, data)


@router.get("/", response_model=PaginatedResponse[GeneroRead])
async def listar_generos_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[GeneroRead]:
    page, size = pag
    return await listar_generos(
        session,
        offset=(page - 1) * size,
        limit=size,
        page=page,
        size=size,
    )


@router.get("/{id}", response_model=GeneroRead)
async def obtener_genero_endpoint(id: int, session: SessionDep) -> GeneroRead:
    return await obtener_genero(session, id)


@router.patch("/{id}", response_model=GeneroRead)
async def actualizar_genero_endpoint(
    id: int, data: GeneroUpdate, session: SessionDep
) -> GeneroRead:
    return await actualizar_genero(session, id, data)
