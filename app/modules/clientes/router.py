"""Rutas HTTP del módulo clientes."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, Paginacion, get_paginacion
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
)
from app.modules.clientes.service import (
    actualizar_cliente,
    crear_cliente,
    crear_perfil,
    listar_clientes,
    listar_ventas_de_cliente,
    obtener_cliente,
)
from app.modules.clientes.unit_of_work import ClientesUnitOfWork
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


async def get_clientes_uow(session: SessionDep) -> ClientesUnitOfWork:
    return ClientesUnitOfWork(session)


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente_endpoint(
    datos: ClienteCreate, uow: ClientesUnitOfWork = Depends(get_clientes_uow)
) -> ClienteRead:
    return await crear_cliente(uow, datos)


@router.get("/", response_model=PaginatedResponse[ClienteRead])
async def listar_clientes_endpoint(
    uow: ClientesUnitOfWork = Depends(get_clientes_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[ClienteRead]:
    return await listar_clientes(uow, pag)


@router.get("/{id}", response_model=ClienteDetalleRead)
async def obtener_cliente_endpoint(
    id: int, uow: ClientesUnitOfWork = Depends(get_clientes_uow)
) -> ClienteDetalleRead:
    return await obtener_cliente(uow, id)


@router.patch("/{id}", response_model=ClienteDetalleRead)
async def actualizar_cliente_endpoint(
    id: int, datos: ClienteUpdate, uow: ClientesUnitOfWork = Depends(get_clientes_uow)
) -> ClienteDetalleRead:
    return await actualizar_cliente(uow, id, datos)


@router.post(
    "/{id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_perfil_cliente_endpoint(
    id: int, datos: PerfilClienteCreate, uow: ClientesUnitOfWork = Depends(get_clientes_uow)
) -> PerfilClienteRead:
    return await crear_perfil(uow, cliente_id=id, datos=datos)


@router.get("/{id}/ventas", response_model=PaginatedResponse[VentaRead])
async def listar_ventas_de_cliente_endpoint(
    id: int,
    uow: ClientesUnitOfWork = Depends(get_clientes_uow),
    pag: Paginacion = Depends(get_paginacion),
) -> PaginatedResponse[VentaRead]:
    return await listar_ventas_de_cliente(uow, id, pag)
