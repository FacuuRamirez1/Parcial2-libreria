"""Rutas HTTP del módulo clientes."""

from fastapi import APIRouter, Depends, status

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, get_paginacion
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
)
from app.modules.clientes.service import (
    actualizar_cliente,
    crear_cliente,
    crear_perfil,
    obtener_clientes,
    obtener_cliente_por_id,
)

router = APIRouter(prefix="/clientes", tags=["clientes"])


@router.post("/", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
async def crear_cliente_endpoint(
    datos: ClienteCreate, session: SessionDep
) -> ClienteRead:
    return await crear_cliente(session, datos)


@router.get("/", response_model=PaginatedResponse[ClienteRead])
async def listar_clientes_endpoint(
    session: SessionDep, pag: tuple[int, int] = Depends(get_paginacion)
) -> PaginatedResponse[ClienteRead]:
    page, size = pag
    return await obtener_clientes(session, page=page, size=size)


@router.get("/{id}", response_model=ClienteRead)
async def obtener_cliente_endpoint(id: int, session: SessionDep) -> ClienteRead:
    return await obtener_cliente_por_id(session, id)


@router.patch("/{id}", response_model=ClienteRead)
async def actualizar_cliente_endpoint(
    id: int, datos: ClienteUpdate, session: SessionDep
) -> ClienteRead:
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
