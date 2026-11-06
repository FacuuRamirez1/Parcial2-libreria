"""Rutas HTTP del módulo editoriales."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.service import (
    actualizar_editorial,
    crear_editorial,
    listar_editoriales,
    obtener_editorial,
)

router = APIRouter(prefix="/editoriales", tags=["editoriales"])


@router.post("/", response_model=EditorialRead, status_code=status.HTTP_201_CREATED)
async def crear_editorial_endpoint(
    data: EditorialCreate, session: SessionDep
) -> EditorialRead:
    return await crear_editorial(session, data)


@router.get("/", response_model=PaginatedResponse[EditorialRead])
async def listar_editoriales_endpoint(
    session: SessionDep, pag: dict = Depends(get_paginacion)
) -> PaginatedResponse[EditorialRead]:
    return await listar_editoriales(
        session,
        offset=pag["offset"],
        limit=pag["limit"],
        page=pag["page"],
        size=pag["size"],
    )


@router.get("/{id}", response_model=EditorialRead)
async def obtener_editorial_endpoint(id: int, session: SessionDep) -> EditorialRead:
    return await obtener_editorial(session, id)


@router.patch("/{id}", response_model=EditorialRead)
async def actualizar_editorial_endpoint(
    id: int, data: EditorialUpdate, session: SessionDep
) -> EditorialRead:
    return await actualizar_editorial(session, id, data)
