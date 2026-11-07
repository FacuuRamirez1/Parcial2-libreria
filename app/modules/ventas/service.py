"""Lógica de negocio del módulo ventas (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.ventas y
uow.session para la consulta de libros (precios) y la alta de venta.
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.clientes.schemas import ClienteRead
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonVentaRead, VentaCreate, VentaRead
from app.modules.ventas.unit_of_work import VentasUnitOfWork

CENTAVOS = Decimal("0.01")
MENSAJE_VENTA_NO_ENCONTRADA = "Venta no encontrada"
MENSAJE_REFERENCIA_INVALIDA = "El cliente o algún libro de la venta no existe"


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


async def crear_venta(uow: VentasUnitOfWork, datos: VentaCreate) -> VentaRead:
    """Crea la venta con sus renglones en una única transacción (commit en el UoW).

    Los precios se leen de la base en una sola consulta; libro/cliente
    inexistente o FK inválida → 409 sin escrituras parciales.
    """
    async with uow:
        ids = [r.libro_id for r in datos.renglones]
        resultado = await uow.session.exec(select(Libro).where(Libro.id.in_(ids)))
        libros = {libro.id: libro for libro in resultado.all()}
        if len(libros) != len(ids):
            raise HTTPException(status_code=409, detail=MENSAJE_REFERENCIA_INVALIDA)

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
            uow.ventas.add(venta)
        except IntegrityError:
            raise HTTPException(status_code=409, detail=MENSAJE_REFERENCIA_INVALIDA)
        return await _obtener_detalle(uow, venta.id)


async def listar_ventas(
    uow: VentasUnitOfWork, pag: Paginacion, cliente_id: int | None = None
) -> PaginatedResponse[VentaRead]:
    async with uow:
        total = await uow.ventas.count(cliente_id=cliente_id)
        verificar_pagina(pag.page, total, pag.size)
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


async def obtener_venta(uow: VentasUnitOfWork, id: int) -> VentaRead:
    async with uow:
        venta = await uow.ventas.get_con_detalle(id)
        if venta is None:
            raise HTTPException(status_code=404, detail=MENSAJE_VENTA_NO_ENCONTRADA)
        return _a_venta_read(venta)


async def _obtener_detalle(uow: VentasUnitOfWork, id: int) -> VentaRead:
    venta = await uow.ventas.get_con_detalle(id)
    if venta is None:
        raise HTTPException(status_code=404, detail=MENSAJE_VENTA_NO_ENCONTRADA)
    return _a_venta_read(venta)
