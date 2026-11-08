"""Rutas HTTP del módulo clientes."""

from fastapi import APIRouter, status

from app.core.database import SessionDep
from app.core.paginacion import PaginacionDep
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
from app.modules.ventas.schemas import VentaRead

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente_endpoint(
    datos: ClienteCreate, session: SessionDep
) -> ClienteRead:
    return await crear_cliente(session, datos)


@router.get("/", response_model=list[ClienteRead])
async def listar_clientes_endpoint(
    session: SessionDep, pag: PaginacionDep
) -> list[ClienteRead]:
    return await listar_clientes(session, pag)


@router.get("/{id}", response_model=ClienteDetalleRead)
async def obtener_cliente_endpoint(id: int, session: SessionDep) -> ClienteDetalleRead:
    return await obtener_cliente(session, id)


@router.patch("/{id}", response_model=ClienteDetalleRead)
async def actualizar_cliente_endpoint(
    id: int, datos: ClienteUpdate, session: SessionDep
) -> ClienteDetalleRead:
    return await actualizar_cliente(session, id, datos)


@router.post(
    "/{id}/perfil",
    response_model=PerfilClienteRead,
    status_code=status.HTTP_201_CREATED,
)
async def crear_perfil_cliente_endpoint(
    id: int, datos: PerfilClienteCreate, session: SessionDep
) -> PerfilClienteRead:
    return await crear_perfil(session, cliente_id=id, datos=datos)


@router.get("/{id}/ventas", response_model=list[VentaRead])
async def listar_ventas_de_cliente_endpoint(
    id: int, session: SessionDep, pag: PaginacionDep
) -> list[VentaRead]:
    return await listar_ventas_de_cliente(session, id, pag)
