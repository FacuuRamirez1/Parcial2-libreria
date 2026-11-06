"""Rutas HTTP del módulo ventas."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.service import crear_venta, obtener_ventas, obtener_venta_por_id

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta_endpoint(
    datos: VentaCreate, session: SessionDep
) -> VentaRead:
    return await crear_venta(session, datos=datos)


@router.get("/", response_model=PaginatedResponse[VentaRead])
async def listar_ventas_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[VentaRead]:
    page, size = pag
    return await obtener_ventas(session, page=page, size=size)


@router.get("/{id}", response_model=VentaRead)
async def obtener_venta_endpoint(id: int, session: SessionDep) -> VentaRead:
    return await obtener_venta_por_id(session, id=id)
