"""Rutas HTTP del módulo editoriales."""

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.service import (
    actualizar_editorial,
    crear_editorial,
    listar_editoriales,
    listar_libros_de_editorial,
    obtener_editorial,
)
from app.modules.libros.schemas import LibroRead

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial_endpoint(
    data: EditorialCreate, session: SessionDep
) -> EditorialRead:
    return await crear_editorial(session, data)


@router.get("/", response_model=list[EditorialRead])
async def listar_editoriales_endpoint(
    session: SessionDep, pag: PaginacionDep
) -> list[EditorialRead]:
    return await listar_editoriales(session, pag)


@router.get("/{id}", response_model=EditorialRead)
async def obtener_editorial_endpoint(id: int, session: SessionDep) -> EditorialRead:
    return await obtener_editorial(session, id)


@router.patch("/{id}", response_model=EditorialRead)
async def actualizar_editorial_endpoint(
    id: int, data: EditorialUpdate, session: SessionDep
) -> EditorialRead:
    return await actualizar_editorial(session, id, data)


@router.get("/{id}/libros", response_model=list[LibroRead])
async def listar_libros_de_editorial_endpoint(
    id: int, session: SessionDep, pag: PaginacionDep
) -> list[LibroRead]:
    return await listar_libros_de_editorial(session, id, pag)
