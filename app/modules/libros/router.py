"""Rutas HTTP del módulo libros."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.libros.schemas import (
    LibroCreate,
    LibroRead,
    LibroUpdate,
    ReponerStockRequest,
)
from app.modules.libros.service import (
    actualizar_libro,
    crear_libro,
    listar_libros,
    obtener_libro,
    reponer_stock,
    soft_delete_libro,
)

router = APIRouter(prefix="/libros", tags=["libros"])


@router.post("/", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
async def crear_libro_endpoint(data: LibroCreate, session: SessionDep) -> LibroRead:
    return await crear_libro(session, data)


@router.get("/", response_model=PaginatedResponse[LibroRead])
async def listar_libros_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[LibroRead]:
    page, size = pag
    return await listar_libros(session, page=page, size=size)


@router.get("/{id}", response_model=LibroRead)
async def obtener_libro_endpoint(id: int, session: SessionDep) -> LibroRead:
    return await obtener_libro(session, id)


@router.patch("/{id}", response_model=LibroRead)
async def actualizar_libro_endpoint(
    id: int, data: LibroUpdate, session: SessionDep
) -> LibroRead:
    return await actualizar_libro(session, id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_libro_endpoint(id: int, session: SessionDep):
    await soft_delete_libro(session, id)
    return None


@router.patch("/{id}/reponer-stock", response_model=LibroRead)
async def reponer_stock_endpoint(
    id: int, data: ReponerStockRequest, session: SessionDep
) -> LibroRead:
    return await reponer_stock(session, id, data.cantidad, data.usuario_id)
