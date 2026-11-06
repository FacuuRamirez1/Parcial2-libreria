"""Lógica de negocio del módulo ventas."""

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, calcular_paginas, verificar_pagina_valida
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.repository import VentaRepository
from app.modules.ventas.schemas import (
    RenglonVentaRead,
    VentaCreate,
    VentaRead,
)


async def crear_venta(session: SessionDep, datos: VentaCreate) -> VentaRead:
    if not datos.renglones:
        raise HTTPException(status_code=400, detail="La venta debe tener al menos un renglón")

    libro_ids = [r.libro_id for r in datos.renglones]
    if len(set(libro_ids)) != len(libro_ids):
        raise HTTPException(status_code=409, detail="Libro repetido en los renglones de la venta")

    # RN-06: leer el precio de cada libro y copiarlo como precio_unitario.
    resultado = await session.exec(select(Libro).where(Libro.id.in_(libro_ids)))
    libros = {libro.id: libro for libro in resultado.all()}
    for renglon in datos.renglones:
        if libros.get(renglon.libro_id) is None:
            raise HTTPException(
                status_code=409, detail=f"Libro {renglon.libro_id} no encontrado"
            )

    total = sum(
        (libros[r.libro_id].precio * r.cantidad for r in datos.renglones),
        Decimal("0"),
    ).quantize(Decimal("0.01"))

    repo = VentaRepository(session, Venta)
    venta = Venta(cliente_id=datos.cliente_id, total=total)
    await repo.add(venta)  # flush: asigna id y rechaza (409) cliente inexistente vía FK

    renglones_creados: list[RenglonVenta] = []
    for renglon in datos.renglones:
        libro = libros[renglon.libro_id]
        r = RenglonVenta(
            venta_id=venta.id,
            libro_id=renglon.libro_id,
            cantidad=renglon.cantidad,
            precio_unitario=libro.precio,
        )
        await repo.add(r)
        renglones_creados.append(r)

    # Sin commit: la transacción la gestiona quien crea la sesión.
    return VentaRead(
        id=venta.id,
        cliente_id=venta.cliente_id,
        fecha=venta.fecha,
        total=venta.total,
        renglones=[
            RenglonVentaRead(
                libro_id=r.libro_id,
                cantidad=r.cantidad,
                precio_unitario=r.precio_unitario,
                subtotal=r.precio_unitario * r.cantidad,
            )
            for r in renglones_creados
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
        .options(selectinload(Venta.renglones))
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
                    RenglonVentaRead(
                        libro_id=r.libro_id,
                        cantidad=r.cantidad,
                        precio_unitario=r.precio_unitario,
                        subtotal=r.precio_unitario * r.cantidad,
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
            RenglonVentaRead(
                libro_id=r.libro_id,
                cantidad=r.cantidad,
                precio_unitario=r.precio_unitario,
                subtotal=r.precio_unitario * r.cantidad,
            )
            for r in venta.renglones
        ],
    )
