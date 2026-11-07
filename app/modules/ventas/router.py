"""Rutas HTTP del módulo ventas."""

from fastapi import APIRouter, BackgroundTasks, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.service import (
    crear_venta,
    enviar_aviso_comprobante,
    listar_ventas,
    obtener_venta,
)

router = APIRouter(prefix="/ventas", tags=["ventas"])


@router.post("/", response_model=VentaRead, status_code=status.HTTP_201_CREATED)
async def crear_venta_endpoint(
    datos: VentaCreate, session: SessionDep, background_tasks: BackgroundTasks
) -> VentaRead:
    venta = await crear_venta(session, datos)
    # El aviso corre después de enviar la respuesta; si falla, la venta ya existe.
    background_tasks.add_task(enviar_aviso_comprobante, venta.id, venta.total)
    return venta


@router.get("/", response_model=list[VentaRead])
async def listar_ventas_endpoint(
    session: SessionDep, pag: PaginacionDep
) -> list[VentaRead]:
    return await listar_ventas(session, pag)


@router.get("/{id}", response_model=VentaRead)
async def obtener_venta_endpoint(id: int, session: SessionDep) -> VentaRead:
    return await obtener_venta(session, id)
