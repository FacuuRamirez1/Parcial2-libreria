"""Lógica de negocio del módulo clientes (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.clientes y
uow.session para la consulta cruzada de ventas del cliente.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.clientes.schemas import (
    ClienteCreate,
    ClienteDetalleRead,
    ClienteRead,
    ClienteUpdate,
    PerfilClienteCreate,
    PerfilClienteRead,
)
from app.modules.clientes.unit_of_work import ClientesUnitOfWork
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonVentaRead, VentaRead

MENSAJE_EMAIL_DUPLICADO = "El email del cliente ya está registrado"
MENSAJE_PERFIL_DUPLICADO = "El cliente ya tiene un perfil asociado"
MENSAJE_CLIENTE_INEXISTENTE = "Cliente no encontrado"

SQLSTATE_UNICO = "23505"
SQLSTATE_CLAVE_FORANEA = "23503"

CENTAVOS = Decimal("0.01")


def _sqlstate(exc: IntegrityError) -> str | None:
    original = exc.orig
    estado = getattr(original, "sqlstate", None)
    if estado:
        return estado
    causa = getattr(original, "__cause__", None)
    return getattr(causa, "sqlstate", None)


def _opciones_venta_detalle() -> tuple:
    return (
        joinedload(Venta.cliente),
        selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
    )


def _subtotal(precio_unitario: Decimal, cantidad: int) -> Decimal:
    return (precio_unitario * cantidad).quantize(CENTAVOS)


def _a_venta_read(venta: Venta) -> VentaRead:
    return VentaRead(
        id=venta.id,
        fecha=venta.fecha,
        total=venta.total,
        cliente=ClienteRead.model_validate(venta.cliente),
        renglones=[
            RenglonVentaRead(
                libro_id=r.libro_id,
                titulo=r.libro.titulo,
                cantidad=r.cantidad,
                precio_unitario=r.precio_unitario,
                subtotal=_subtotal(r.precio_unitario, r.cantidad),
            )
            for r in venta.renglones
        ],
    )


async def _leer_con_perfil(uow: ClientesUnitOfWork, id: int) -> Cliente:
    resultado = await uow.session.exec(
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


async def crear_cliente(uow: ClientesUnitOfWork, datos: ClienteCreate) -> ClienteRead:
    try:
        async with uow:
            cliente = Cliente(**datos.model_dump())
            await uow.clientes.add(cliente)  # flush: dispara el UNIQUE de email
    except IntegrityError:
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)
    return ClienteRead.model_validate(cliente)


async def listar_clientes(uow: ClientesUnitOfWork, pag: Paginacion) -> PaginatedResponse[ClienteRead]:
    async with uow:
        total = await uow.clientes.count()
        verificar_pagina(pag.page, pag.size, total)
        items = await uow.clientes.get_all(offset=pag.offset, limit=pag.limit)
        return PaginatedResponse(
            items=[ClienteRead.model_validate(c) for c in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )


async def obtener_cliente(uow: ClientesUnitOfWork, id: int) -> ClienteDetalleRead:
    async with uow:
        return _a_detalle(await _leer_con_perfil(uow, id))


async def actualizar_cliente(
    uow: ClientesUnitOfWork, id: int, datos: ClienteUpdate
) -> ClienteDetalleRead:
    try:
        async with uow:
            cliente = await uow.session.get(Cliente, id)
            if cliente is None:
                raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
            for campo, valor in datos.model_dump(exclude_unset=True).items():
                setattr(cliente, campo, valor)
            await uow.clientes.update(cliente)  # flush: dispara el UNIQUE de email
            resultado = await uow.session.exec(
                select(Cliente)
                .where(Cliente.id == id)
                .options(joinedload(Cliente.perfil))
            )
            cliente = resultado.first()
    except IntegrityError:
        raise HTTPException(status_code=409, detail=MENSAJE_EMAIL_DUPLICADO)
    return _a_detalle(cliente)


async def crear_perfil(
    uow: ClientesUnitOfWork, cliente_id: int, datos: PerfilClienteCreate
) -> PerfilClienteRead:
    try:
        async with uow:
            perfil = PerfilCliente(
                cliente_id=cliente_id,
                telefono=datos.telefono,
                direccion=datos.direccion,
            )
            uow.session.add(perfil)
            await uow.session.flush()  # dispara UNIQUE (perfil) o FK (cliente)
    except IntegrityError as exc:
        estado = _sqlstate(exc)
        if estado == SQLSTATE_UNICO:
            raise HTTPException(status_code=409, detail=MENSAJE_PERFIL_DUPLICADO)
        if estado == SQLSTATE_CLAVE_FORANEA:
            raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
        raise
    return PerfilClienteRead.model_validate(perfil)


async def listar_ventas_de_cliente(
    uow: ClientesUnitOfWork, id: int, pag: Paginacion
) -> PaginatedResponse[VentaRead]:
    async with uow:
        if await uow.session.get(Cliente, id) is None:
            raise HTTPException(status_code=404, detail=MENSAJE_CLIENTE_INEXISTENTE)
        consulta = select(Venta).options(*_opciones_venta_detalle()).where(
            Venta.cliente_id == id
        )
        total = await uow.session.exec(
            select(func.count()).select_from(Venta).where(Venta.cliente_id == id)
        )
        total = total.one()
        verificar_pagina(pag.page, pag.size, total)
        resultado = await uow.session.exec(
            consulta.order_by(Venta.id).offset(pag.offset).limit(pag.limit)
        )
        items = resultado.all()
        return PaginatedResponse(
            items=[_a_venta_read(v) for v in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )
