"""Rutas HTTP del módulo generos."""

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.generos.service import (
    actualizar_genero,
    crear_genero,
    listar_generos,
    listar_libros_de_genero,
    obtener_genero,
)
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/generos", tags=["generos"])


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero_endpoint(data: GeneroCreate, session: SessionDep) -> GeneroRead:
    return await crear_genero(session, data)


@router.get("/", response_model=list[GeneroRead])
async def listar_generos_endpoint(
    session: SessionDep, pag: PaginacionDep
) -> list[GeneroRead]:
    return await listar_generos(session, pag)


@router.get("/{id}", response_model=GeneroRead)
async def obtener_genero_endpoint(id: int, session: SessionDep) -> GeneroRead:
    return await obtener_genero(session, id)


@router.patch("/{id}", response_model=GeneroRead)
async def actualizar_genero_endpoint(
    id: int, data: GeneroUpdate, session: SessionDep
) -> GeneroRead:
    return await actualizar_genero(session, id, data)


@router.get("/{id}/libros", response_model=list[LibroRead])
async def listar_libros_de_genero_endpoint(
    id: int, session: SessionDep, pag: PaginacionDep
) -> list[LibroRead]:
    return await listar_libros_de_genero(session, id, pag)
