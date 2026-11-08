"""Rutas HTTP del módulo libros."""

from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
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

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=LibroDetalleRead, status_code=status.HTTP_201_CREATED)
async def crear_libro_endpoint(
    data: LibroCreate, session: SessionDep
) -> LibroDetalleRead:
    return await crear_libro(session, data)


@router.get("/", response_model=list[LibroListaRead])
async def listar_libros_endpoint(
    session: SessionDep,
    pag: PaginacionDep,
    titulo: Annotated[str | None, Query(max_length=255)] = None,
    genero_id: Annotated[int | None, Query()] = None,
) -> list[LibroListaRead]:
    return await listar_libros(session, pag, titulo=titulo, genero_id=genero_id)


@router.get("/{id}", response_model=LibroDetalleRead)
async def obtener_libro_endpoint(id: int, session: SessionDep) -> LibroDetalleRead:
    return await obtener_libro(session, id)


@router.patch("/{id}", response_model=LibroDetalleRead)
async def actualizar_libro_endpoint(
    id: int, data: LibroUpdate, session: SessionDep
) -> LibroDetalleRead:
    return await actualizar_libro(session, id, data)
