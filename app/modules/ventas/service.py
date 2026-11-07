"""Lógica de negocio del módulo ventas."""

import asyncio
import logging
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, calcular_paginas, verificar_pagina_valida
from app.core.unit_of_work import UnitOfWork
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.repository import VentaRepository
from app.modules.ventas.schemas import (
    RenglonVentaRead,
    VentaCreate,
    VentaRead,
)

CENTAVOS = Decimal("0.01")
logger = logging.getLogger(__name__)


async def _esperar_aviso() -> None:
    """Pausa no bloqueante del aviso; aislada para poder controlarla en tests."""
    await asyncio.sleep(0.5)


async def enviar_aviso_comprobante(venta_id: int, total: Decimal) -> None:
    """Aviso simulado que corre en segundo plano, después de responder la venta."""
    await _esperar_aviso()
    logger.info("Aviso de comprobante enviado: venta=%s total=%s", venta_id, total)


def _calcular_subtotal(precio_unitario: Decimal, cantidad: int) -> Decimal:
    return (precio_unitario * cantidad).quantize(CENTAVOS)


def _a_renglon_read(
    libro_id: int, titulo: str, cantidad: int, precio_unitario: Decimal
) -> RenglonVentaRead:
    return RenglonVentaRead(
        libro_id=libro_id,
        titulo=titulo,
        cantidad=cantidad,
        precio_unitario=precio_unitario,
        subtotal=_calcular_subtotal(precio_unitario, cantidad),
    )


async def crear_venta(session: SessionDep, datos: VentaCreate) -> VentaRead:
    """Crea la venta y sus renglones en una única transacción.

    La validación de renglones (no vacío, sin libro repetido, cantidad > 0) ya
    la hizo el DTO. Se leen los precios en una sola consulta (RN-06) y se deja
    que la FK rechace un cliente inexistente (409 vía handler global).
    """
    libro_ids = [renglon.libro_id for renglon in datos.renglones]
    resultado = await session.exec(select(Libro).where(Libro.id.in_(libro_ids)))
    libros = {libro.id: libro for libro in resultado.all()}
    for renglon in datos.renglones:
        if libros.get(renglon.libro_id) is None:
            raise HTTPException(status_code=409, detail="Libro no encontrado")

    total = sum(
        (_calcular_subtotal(libros[r.libro_id].precio, r.cantidad) for r in datos.renglones),
        Decimal("0"),
    ).quantize(CENTAVOS)

    repo = VentaRepository(session, Venta)
    async with UnitOfWork(session):
        venta = Venta(cliente_id=datos.cliente_id, total=total)
        await repo.add(venta)  # flush: asigna id y la FK rechaza cliente inexistente
        for renglon in datos.renglones:
            libro = libros[renglon.libro_id]
            session.add(
                RenglonVenta(
                    venta_id=venta.id,
                    libro_id=renglon.libro_id,
                    cantidad=renglon.cantidad,
                    precio_unitario=libro.precio,
                )
            )
        await session.flush()

    return VentaRead(
        id=venta.id,
        cliente_id=venta.cliente_id,
        fecha=venta.fecha,
        total=venta.total,
        renglones=[
            _a_renglon_read(
                libro_id=renglon.libro_id,
                titulo=libros[renglon.libro_id].titulo,
                cantidad=renglon.cantidad,
                precio_unitario=libros[renglon.libro_id].precio,
            )
            for renglon in datos.renglones
        ],
    )


async def obtener_ventas(
    session: SessionDep, page: int, size: int
) -> PaginatedResponse[VentaRead]:
    repo = VentaRepository(session, Venta)
    total = await repo.count()
    pages = calcular_paginas(total, size)
    verificar_pagina_valida(page, pages, total)

    offset = (page - 1) * size
    statement = (
        select(Venta)
        .options(selectinload(Venta.renglones).joinedload(RenglonVenta.libro))
        .offset(offset)
        .limit(size)
    )
    resultado = await session.exec(statement)
    items = resultado.all()

    return PaginatedResponse[VentaRead](
        items=[
            VentaRead(
                id=v.id,
                cliente_id=v.cliente_id,
                fecha=v.fecha,
                total=v.total,
                renglones=[
                    _a_renglon_read(
                        libro_id=r.libro_id,
                        titulo=r.libro.titulo,
                        cantidad=r.cantidad,
                        precio_unitario=r.precio_unitario,
                    )
                    for r in v.renglones
                ],
            )
            for v in items
        ],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


async def obtener_venta_por_id(session: SessionDep, id: int) -> VentaRead:
    repo = VentaRepository(session, Venta)
    venta = await repo.get_con_detalle(id)
    if venta is None:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return VentaRead(
        id=venta.id,
        cliente_id=venta.cliente_id,
        fecha=venta.fecha,
        total=venta.total,
        renglones=[
            _a_renglon_read(
                libro_id=r.libro_id,
                titulo=r.libro.titulo,
                cantidad=r.cantidad,
                precio_unitario=r.precio_unitario,
            )
            for r in venta.renglones
        ],
    )
