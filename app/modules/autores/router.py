"""Rutas HTTP del módulo autores."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.autores.service import (
    actualizar_autor,
    crear_autor,
    listar_autores,
    listar_libros_de_autor,
    obtener_autor,
)
from app.modules.autores.unit_of_work import AutoresUnitOfWork
from app.modules.libros.schemas import LibroDeAutorRead

router = APIRouter(prefix="/autores", tags=["autores"])


async def get_autores_uow(session: SessionDep) -> AutoresUnitOfWork:
    return AutoresUnitOfWork(session)


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor_endpoint(
    data: AutorCreate, uow: AutoresUnitOfWork = Depends(get_autores_uow)
) -> AutorRead:
    return await crear_autor(uow, data)


@router.get("/", response_model=PaginatedResponse[AutorRead])
async def listar_autores_endpoint(
    uow: AutoresUnitOfWork = Depends(get_autores_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[AutorRead]:
    return await listar_autores(uow, pag)


@router.get("/{id}", response_model=AutorRead)
async def obtener_autor_endpoint(
    id: int, uow: AutoresUnitOfWork = Depends(get_autores_uow)
) -> AutorRead:
    return await obtener_autor(uow, id)


@router.patch("/{id}", response_model=AutorRead)
async def actualizar_autor_endpoint(
    id: int, data: AutorUpdate, uow: AutoresUnitOfWork = Depends(get_autores_uow)
) -> AutorRead:
    return await actualizar_autor(uow, id, data)


@router.get("/{id}/libros", response_model=PaginatedResponse[LibroDeAutorRead])
async def listar_libros_de_autor_endpoint(
    id: int,
    uow: AutoresUnitOfWork = Depends(get_autores_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[LibroDeAutorRead]:
    return await listar_libros_de_autor(uow, id, pag)
