"""Rutas HTTP del módulo ventas."""

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.core.database import SessionDep
from app.core.dependencies import ADMIN, PERSONAL, UsuarioActual, UsuarioActualDep, requiere_rol
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.ventas.schemas import VentaCreate, VentaRead
from app.modules.ventas.service import (
    crear_venta,
    enviar_aviso_comprobante,
    listar_ventas,
    listar_ventas_propias,
    obtener_venta,
)
from app.modules.ventas.unit_of_work import VentasUnitOfWork

router_protegido = APIRouter(prefix="/ventas", tags=["ventas"])
router_mis_ventas = APIRouter(prefix="/mis-ventas", tags=["ventas"])


async def get_ventas_uow(session: SessionDep) -> VentasUnitOfWork:
    return VentasUnitOfWork(session)


@router_protegido.post(
    "/",
    response_model=VentaRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_venta_endpoint(
    datos: VentaCreate,
    background_tasks: BackgroundTasks,
    actual: UsuarioActual = Depends(requiere_rol(*PERSONAL)),
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
) -> VentaRead:
    venta = await crear_venta(uow, datos, actual.usuario.id)
    # El aviso corre después de enviar la respuesta; solo si la venta se confirmó.
    background_tasks.add_task(enviar_aviso_comprobante, venta.id, venta.total)
    return venta


# Listado completo de ventas: solo ADMIN (S-02).
@router_protegido.get(
    "/",
    dependencies=[Depends(requiere_rol(ADMIN))],
    response_model=PaginatedResponse[VentaRead],
)
async def listar_ventas_endpoint(
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[VentaRead]:
    return await listar_ventas(uow, pag)


@router_mis_ventas.get("", response_model=PaginatedResponse[VentaRead])
async def listar_ventas_propias_endpoint(
    actual: UsuarioActualDep,
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[VentaRead]:
    return await listar_ventas_propias(uow, pag, actual)


# El detalle no lleva `requiere_rol`: lo decide el servicio (personal o dueño).
@router_protegido.get("/{id}", response_model=VentaRead)
async def obtener_venta_endpoint(
    id: int,
    actual: UsuarioActualDep,
    uow: VentasUnitOfWork = Depends(get_ventas_uow),
) -> VentaRead:
    return await obtener_venta(uow, id, actual)
