"""Rutas HTTP del módulo autores."""

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.autores.service import (
    actualizar_autor,
    crear_autor,
    listar_autores,
    listar_libros_de_autor,
    obtener_autor,
)
from app.modules.libros.schemas import LibroDeAutorRead

router = APIRouter(prefix="/autores", tags=["autores"])


@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
async def crear_autor_endpoint(data: AutorCreate, session: SessionDep) -> AutorRead:
    return await crear_autor(session, data)


@router.get("/", response_model=list[AutorRead])
async def listar_autores_endpoint(
    session: SessionDep, pag: PaginacionDep
) -> list[AutorRead]:
    return await listar_autores(session, pag)


@router.get("/{id}", response_model=AutorRead)
async def obtener_autor_endpoint(id: int, session: SessionDep) -> AutorRead:
    return await obtener_autor(session, id)


@router.patch("/{id}", response_model=AutorRead)
async def actualizar_autor_endpoint(
    id: int, data: AutorUpdate, session: SessionDep
) -> AutorRead:
    return await actualizar_autor(session, id, data)


@router.get("/{id}/libros", response_model=list[LibroDeAutorRead])
async def listar_libros_de_autor_endpoint(
    id: int, session: SessionDep, pag: PaginacionDep
) -> list[LibroDeAutorRead]:
    return await listar_libros_de_autor(session, id, pag)
