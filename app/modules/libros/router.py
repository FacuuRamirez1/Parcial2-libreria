"""Rutas HTTP del módulo libros."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.database import SessionDep
from app.core.dependencies import ADMIN, requiere_rol
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.libros.schemas import (
    LibroCreate,
    LibroDetalleRead,
    LibroListaRead,
    LibroUpdate,
)
from app.modules.libros.service import (
    actualizar_libro,
    crear_libro,
    listar_libros,
    obtener_libro,
)
from app.modules.libros.unit_of_work import LibrosUnitOfWork

router_abierto = APIRouter(prefix="/libros", tags=["libros"])
router_protegido = APIRouter(prefix="/libros", tags=["libros"])


async def get_libros_uow(session: SessionDep) -> LibrosUnitOfWork:
    return LibrosUnitOfWork(session)


@router_protegido.post("/", dependencies=[Depends(requiere_rol(ADMIN))], response_model=LibroDetalleRead, status_code=status.HTTP_201_CREATED)
async def crear_libro_endpoint(
    data: LibroCreate, uow: LibrosUnitOfWork = Depends(get_libros_uow)
) -> LibroDetalleRead:
    return await crear_libro(uow, data)


@router_abierto.get("/", response_model=PaginatedResponse[LibroListaRead])
async def listar_libros_endpoint(
    uow: LibrosUnitOfWork = Depends(get_libros_uow),
    pag: Paginacion = Depends(get_paginacion),
    titulo: Annotated[str | None, Query(max_length=255)] = None,
    genero_id: Annotated[int | None, Query()] = None,
) -> PaginatedResponse[LibroListaRead]:
    return await listar_libros(uow, pag, titulo=titulo, genero_id=genero_id)


@router_abierto.get("/{id}", response_model=LibroDetalleRead)
async def obtener_libro_endpoint(
    id: int, uow: LibrosUnitOfWork = Depends(get_libros_uow)
) -> LibroDetalleRead:
    return await obtener_libro(uow, id)


@router_protegido.patch("/{id}", dependencies=[Depends(requiere_rol(ADMIN))], response_model=LibroDetalleRead)
async def actualizar_libro_endpoint(
    id: int, data: LibroUpdate, uow: LibrosUnitOfWork = Depends(get_libros_uow)
) -> LibroDetalleRead:
    return await actualizar_libro(uow, id, data)
