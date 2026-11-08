"""Lógica de negocio del módulo ventas (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.ventas y
uow.session para la consulta de libros (precios y stock) y la alta de venta.
La venta, sus renglones, el descuento de stock y un movimiento por renglón se
escriben en un solo Unit of Work (RN-10).
"""

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.dependencies import PERSONAL, UsuarioActual
from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.clientes.repository import ClienteRepository
from app.modules.clientes.schemas import ClienteRead
from app.modules.libros.models import Libro
from app.modules.libros.stock import registrar_movimiento
from app.modules.usuarios.repository import AsignacionRolRepository
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonVentaRead, VentaCreate, VentaRead
from app.modules.ventas.unit_of_work import VentasUnitOfWork

CENTAVOS = Decimal("0.01")
MENSAJE_VENTA_NO_ENCONTRADA = "Venta no encontrada"
MENSAJE_REFERENCIA_INVALIDA = "El cliente o algún libro de la venta no existe"
MENSAJE_STOCK_INSUFICIENTE = "No hay stock suficiente para la venta"
MENSAJE_SIN_PERMISO = "No tenés permiso para ver esta venta"
logger = logging.getLogger(__name__)


async def _esperar_aviso() -> None:
    """Pausa no bloqueante del aviso; aislada para poder controlarla en tests."""
    await asyncio.sleep(0.5)


async def enviar_aviso_comprobante(venta_id: int, total: Decimal) -> None:
    """Aviso simulado que corre en segundo plano, después de responder la venta."""
    await _esperar_aviso()
    logger.info("Aviso de comprobante enviado: venta=%s total=%s", venta_id, total)


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


async def crear_venta(
    uow: VentasUnitOfWork, datos: VentaCreate, usuario_id: int
) -> VentaRead:
    """Crea la venta, sus renglones, el descuento y los movimientos en un solo UoW.

    Los precios y el stock se leen de la base en una sola consulta de libros
    vigentes; libro/cliente inexistente, libro dado de baja o stock insuficiente
    → 409 sin escrituras parciales.
    """
    async with uow:
        ids = [r.libro_id for r in datos.renglones]
        resultado = await uow.session.exec(
            select(Libro)
            .where(Libro.id.in_(ids))
            .where(Libro.borrado_en.is_(None))
        )
        libros = {libro.id: libro for libro in resultado.all()}
        if len(libros) != len(ids):
            raise HTTPException(status_code=409, detail=MENSAJE_REFERENCIA_INVALIDA)

        for renglon in datos.renglones:
            if libros[renglon.libro_id].stock < renglon.cantidad:
                raise HTTPException(status_code=409, detail=MENSAJE_STOCK_INSUFICIENTE)

        total = sum(
            (_subtotal(libros[r.libro_id].precio, r.cantidad) for r in datos.renglones),
            Decimal("0"),
        ).quantize(CENTAVOS)

        venta = Venta(
            cliente_id=datos.cliente_id,
            total=total,
            renglones=[
                RenglonVenta(
                    libro_id=r.libro_id,
                    cantidad=r.cantidad,
                    precio_unitario=libros[r.libro_id].precio,
                )
                for r in datos.renglones
            ],
        )
        try:
            await uow.ventas.add(venta)
        except IntegrityError:
            raise HTTPException(status_code=409, detail=MENSAJE_REFERENCIA_INVALIDA)

        for renglon in datos.renglones:
            await registrar_movimiento(
                uow,
                libro=libros[renglon.libro_id],
                cantidad=-renglon.cantidad,
                motivo="Venta",
                usuario_id=usuario_id,
                venta_id=venta.id,
            )

        return await _obtener_detalle(uow, venta.id)


async def listar_ventas(
    uow: VentasUnitOfWork, pag: Paginacion, cliente_id: int | None = None
) -> PaginatedResponse[VentaRead]:
    async with uow:
        return await _listar(uow, pag, cliente_id)


async def listar_ventas_propias(
    uow: VentasUnitOfWork, pag: Paginacion, actual: UsuarioActual
) -> PaginatedResponse[VentaRead]:
    """Ventas del cliente asociado al usuario; sin ficha de cliente, página vacía."""
    async with uow:
        cliente = await ClienteRepository(uow.session).get_by_usuario_id(actual.usuario.id)
        if cliente is None:
            return PaginatedResponse(
                items=[],
                total=0,
                page=pag.page,
                size=pag.size,
                pages=calcular_paginas(0, pag.size),
            )
        return await _listar(uow, pag, cliente.id)


async def _listar(
    uow: VentasUnitOfWork, pag: Paginacion, cliente_id: int | None
) -> PaginatedResponse[VentaRead]:
    total = await uow.ventas.count(cliente_id=cliente_id)
    verificar_pagina(pag.page, pag.size, total)
    items = await uow.ventas.get_all(
        offset=pag.offset, limit=pag.limit, cliente_id=cliente_id
    )
    return PaginatedResponse(
        items=[_a_venta_read(v) for v in items],
        total=total,
        page=pag.page,
        size=pag.size,
        pages=calcular_paginas(total, pag.size),
    )


async def obtener_venta(
    uow: VentasUnitOfWork, id: int, actual: UsuarioActual
) -> VentaRead:
    """Detalle permitido al personal vigente o al cliente dueño; si no, 403 (RN-14)."""
    async with uow:
        venta = await uow.ventas.get_con_detalle(id)
        if venta is None:
            raise HTTPException(status_code=404, detail=MENSAJE_VENTA_NO_ENCONTRADA)

        roles = await AsignacionRolRepository(uow.session).roles_vigentes(
            actual.usuario.id, datetime.now(UTC)
        )
        es_personal = not set(roles).isdisjoint(PERSONAL)
        es_duenio = venta.cliente.usuario_id == actual.usuario.id
        if not (es_personal or es_duenio):
            raise HTTPException(status_code=403, detail=MENSAJE_SIN_PERMISO)

        return _a_venta_read(venta)


async def _obtener_detalle(uow: VentasUnitOfWork, id: int) -> VentaRead:
    venta = await uow.ventas.get_con_detalle(id)
    if venta is None:
        raise HTTPException(status_code=404, detail=MENSAJE_VENTA_NO_ENCONTRADA)
    return _a_venta_read(venta)
