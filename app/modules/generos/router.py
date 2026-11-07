"""Rutas HTTP del módulo generos."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.generos.service import (
    actualizar_genero,
    crear_genero,
    listar_generos,
    listar_libros_de_genero,
    obtener_genero,
)
from app.modules.generos.unit_of_work import GenerosUnitOfWork
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/generos", tags=["generos"])


async def get_generos_uow(session: SessionDep) -> GenerosUnitOfWork:
    return GenerosUnitOfWork(session)


@router.post("/", response_model=GeneroRead, status_code=status.HTTP_201_CREATED)
async def crear_genero_endpoint(
    data: GeneroCreate, uow: GenerosUnitOfWork = Depends(get_generos_uow)
) -> GeneroRead:
    return await crear_genero(uow, data)


@router.get("/", response_model=PaginatedResponse[GeneroRead])
async def listar_generos_endpoint(
    uow: GenerosUnitOfWork = Depends(get_generos_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[GeneroRead]:
    return await listar_generos(uow, pag)


@router.get("/{id}", response_model=GeneroRead)
async def obtener_genero_endpoint(
    id: int, uow: GenerosUnitOfWork = Depends(get_generos_uow)
) -> GeneroRead:
    return await obtener_genero(uow, id)


@router.patch("/{id}", response_model=GeneroRead)
async def actualizar_genero_endpoint(
    id: int, data: GeneroUpdate, uow: GenerosUnitOfWork = Depends(get_generos_uow)
) -> GeneroRead:
    return await actualizar_genero(uow, id, data)


@router.get("/{id}/libros", response_model=PaginatedResponse[LibroRead])
async def listar_libros_de_genero_endpoint(
    id: int,
    uow: GenerosUnitOfWork = Depends(get_generos_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[LibroRead]:
    return await listar_libros_de_genero(uow, id, pag)
