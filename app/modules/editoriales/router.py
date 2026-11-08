"""Rutas HTTP del módulo editoriales."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.dependencies import ADMIN, requiere_rol
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.service import (
    actualizar_editorial,
    crear_editorial,
    listar_editoriales,
    listar_libros_de_editorial,
    obtener_editorial,
)
from app.modules.editoriales.unit_of_work import EditorialesUnitOfWork
from app.modules.libros.schemas import LibroRead

router_abierto = APIRouter(prefix="/editoriales", tags=["editoriales"])
router_protegido = APIRouter(prefix="/editoriales", tags=["editoriales"])


async def get_editoriales_uow(session: SessionDep) -> EditorialesUnitOfWork:
    return EditorialesUnitOfWork(session)


@router_protegido.post("/", dependencies=[Depends(requiere_rol(ADMIN))], response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial_endpoint(
    data: EditorialCreate, uow: EditorialesUnitOfWork = Depends(get_editoriales_uow)
) -> EditorialRead:
    return await crear_editorial(uow, data)


@router_abierto.get("/", response_model=PaginatedResponse[EditorialRead])
async def listar_editoriales_endpoint(
    uow: EditorialesUnitOfWork = Depends(get_editoriales_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[EditorialRead]:
    return await listar_editoriales(uow, pag)


@router_abierto.get("/{id}", response_model=EditorialRead)
async def obtener_editorial_endpoint(
    id: int, uow: EditorialesUnitOfWork = Depends(get_editoriales_uow)
) -> EditorialRead:
    return await obtener_editorial(uow, id)


@router_protegido.patch("/{id}", dependencies=[Depends(requiere_rol(ADMIN))], response_model=EditorialRead)
async def actualizar_editorial_endpoint(
    id: int, data: EditorialUpdate, uow: EditorialesUnitOfWork = Depends(get_editoriales_uow)
) -> EditorialRead:
    return await actualizar_editorial(uow, id, data)


@router_abierto.get("/{id}/libros", response_model=PaginatedResponse[LibroRead])
async def listar_libros_de_editorial_endpoint(
    id: int,
    uow: EditorialesUnitOfWork = Depends(get_editoriales_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[LibroRead]:
    return await listar_libros_de_editorial(uow, id, pag)
