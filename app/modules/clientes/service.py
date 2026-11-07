"""Lógica de negocio del módulo clientes (recibe la sesión como parámetro)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
)
from app.modules.ventas.schemas import VentaRead
from app.modules.ventas.service import listar_ventas

MENSAJE_EMAIL_DUPLICADO = "El email del cliente ya está registrado"
MENSAJE_PERFIL_DUPLICADO = "El cliente ya tiene un perfil asociado"
MENSAJE_CLIENTE_INEXISTENTE = "Cliente no encontrado"

SQLSTATE_UNICO = "23505"
SQLSTATE_CLAVE_FORANEA = "23503"


def _sqlstate(exc: IntegrityError) -> str | None:
    """Extrae el SQLSTATE del error del driver sin exponerlo en la respuesta."""
    original = exc.orig
    estado = getattr(original, "sqlstate", None)
    if estado:
        return estado
    causa = getattr(original, "__cause__", None)
    return getattr(causa, "sqlstate", None)


async def _confirmar_email_unico(session: SessionDep) -> None:
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)


async def _leer_con_perfil(session: SessionDep, id: int) -> Cliente:
    """Cliente con su perfil en la misma consulta (joinedload: relación a uno)."""
    resultado = await session.exec(
        select(Cliente)
        .where(Cliente.id == id)
        .options(joinedload(Cliente.perfil))
        .execution_options(populate_existing=True)
    )
    cliente = resultado.first()
    if cliente is None:
        raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
    return cliente


def _a_detalle(cliente: Cliente) -> ClienteDetalleRead:
    return ClienteDetalleRead(
        **ClienteRead.model_validate(cliente).model_dump(),
        perfil=(
            PerfilClienteRead.model_validate(cliente.perfil)
            if cliente.perfil
            else None
        ),
    )


async def crear_cliente(session: SessionDep, datos: ClienteCreate) -> ClienteRead:
    cliente = Cliente(**datos.model_dump())
    session.add(cliente)
    await _confirmar_email_unico(session)
    return ClienteRead.model_validate(cliente)


async def listar_clientes(session: SessionDep, pag: Paginacion) -> list[ClienteRead]:
    resultado = await session.exec(
        select(Cliente).order_by(Cliente.id).offset(pag.offset).limit(pag.limit)
    )
    return [ClienteRead.model_validate(c) for c in resultado.all()]


async def obtener_cliente(session: SessionDep, id: int) -> ClienteDetalleRead:
    return _a_detalle(await _leer_con_perfil(session, id))


async def actualizar_cliente(
    session: SessionDep, id: int, datos: ClienteUpdate
) -> ClienteDetalleRead:
    cliente = await session.get(Cliente, id)
    if cliente is None:
        raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(cliente, campo, valor)
    await _confirmar_email_unico(session)
    return await obtener_cliente(session, id)


async def crear_perfil(
    session: SessionDep, cliente_id: int, datos: PerfilClienteCreate
) -> PerfilClienteRead:
    """Crea el perfil único del cliente indicado en la ruta.

    No se consulta si el cliente existe: la FK lo rechaza. El SQLSTATE distingue
    el perfil duplicado (UNIQUE, 409) del cliente inexistente (FK, 404).
    """
    perfil = PerfilCliente(
        cliente_id=cliente_id,
        telefono=datos.telefono,
        direccion=datos.direccion,
    )
    session.add(perfil)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        estado = _sqlstate(exc)
        if estado == SQLSTATE_UNICO:
            raise HTTPException(status_code=409, detail=MENSAJE_PERFIL_DUPLICADO)
        if estado == SQLSTATE_CLAVE_FORANEA:
            raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
        raise
    return PerfilClienteRead.model_validate(perfil)


async def listar_ventas_de_cliente(
    session: SessionDep, id: int, pag: Paginacion
) -> list[VentaRead]:
    if await session.get(Cliente, id) is None:
        raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
    return await listar_ventas(session, pag, cliente_id=id)
