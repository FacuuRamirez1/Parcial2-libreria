"""Rutas HTTP del módulo ventas."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.service import (
    crear_venta,
    enviar_aviso_comprobante,
    listar_ventas,
    obtener_venta,
)
from app.modules.ventas.unit_of_work import VentasUnitOfWork

router = APIRouter(prefix="/ventas", tags=["ventas"])


async def get_ventas_uow(session: SessionDep) -> VentasUnitOfWork:
    return VentasUnitOfWork(session)


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta_endpoint(
    datos: VentaCreate,
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
    background_tasks: BackgroundTasks = None,
) -> VentaRead:
    venta = await crear_venta(uow, datos)
    # El aviso corre después de enviar la respuesta; solo si la venta se confirmó.
    background_tasks.add_task(enviar_aviso_comprobante, venta.id, venta.total)
    return venta


@router.get("/", response_model=PaginatedResponse[VentaRead])
async def listar_ventas_endpoint(
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[VentaRead]:
    return await listar_ventas(uow, pag)


@router.get("/{id}", response_model=VentaRead)
async def obtener_venta_endpoint(
    id: int, uow: VentasUnitOfWork = Depends(get_ventas_uow)
) -> VentaRead:
    return await obtener_venta(uow, id)
