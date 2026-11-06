"""Lógica de negocio del módulo clientes."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, paginar
from app.core.repository import BaseRepository
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
)


async def crear_cliente(session: SessionDep, datos: ClienteCreate) -> ClienteRead:
    repo = BaseRepository(session, Cliente)
    cliente = Cliente(**datos.model_dump())
    try:
        await repo.add(cliente)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="El email del cliente ya está registrado"
        )
    return ClienteRead.model_validate(cliente)


async def obtener_clientes(
    session: SessionDep, page: int, size: int
) -> PaginatedResponse[ClienteRead]:
    repo = BaseRepository(session, Cliente)
    total = await repo.count()
    offset = (page - 1) * size
    items = await repo.get_all(offset=offset, limit=size)
    return paginar(
        [ClienteRead.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
    )


async def obtener_cliente_por_id(session: SessionDep, id: int) -> ClienteRead:
    repo = BaseRepository(session, Cliente)
    cliente = await repo.get_by_id(id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ClienteRead.model_validate(cliente)


async def actualizar_cliente(
    session: SessionDep, id: int, datos: ClienteUpdate
) -> ClienteRead:
    repo = BaseRepository(session, Cliente)
    cliente = await repo.get_by_id(id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, key, value)
    try:
        await repo.update(cliente)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="El email del cliente ya está registrado"
        )
    return ClienteRead.model_validate(cliente)


async def crear_perfil(
    session: SessionDep, cliente_id: int, datos: PerfilClienteCreate
) -> PerfilClienteRead:
    repo = BaseRepository(session, PerfilCliente)
    perfil = PerfilCliente(
        cliente_id=cliente_id,
        telefono=datos.telefono,
        direccion=datos.direccion,
    )
    try:
        await repo.add(perfil)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=409, detail="El cliente ya tiene un perfil asociado"
        )
    return PerfilClienteRead.model_validate(perfil)
