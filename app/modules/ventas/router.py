"""Rutas HTTP del módulo ventas."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.service import (
    crear_venta,
    enviar_aviso_comprobante,
    obtener_venta_por_id,
    obtener_ventas,
)

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta_endpoint(
    datos: VentaCreate, session: SessionDep, background_tasks: BackgroundTasks
) -> VentaRead:
    venta = await crear_venta(session, datos=datos)
    background_tasks.add_task(enviar_aviso_comprobante, venta.id, venta.total)
    return venta


@router.get("/", response_model=PaginatedResponse[VentaRead])
async def listar_ventas_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[VentaRead]:
    page, size = pag
    return await obtener_ventas(session, page=page, size=size)


@router.get("/{id}", response_model=VentaRead)
async def obtener_venta_endpoint(id: int, session: SessionDep) -> VentaRead:
    return await obtener_venta_por_id(session, id=id)
