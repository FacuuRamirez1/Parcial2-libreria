"""Lógica de negocio del módulo ventas (recibe la sesión como parámetro)."""

import asyncio
import logging
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
from app.modules.clientes.schemas import ClienteRead
from app.modules.libros.models import Libro
from app.modules.ventas.models import RenglonVenta, Venta
from app.modules.ventas.schemas import RenglonVentaRead, VentaCreate, VentaRead

CENTAVOS = Decimal("0.01")
MENSAJE_VENTA_NO_ENCONTRADA = "Venta no encontrada"
MENSAJE_REFERENCIA_INVALIDA = "El cliente o algún libro de la venta no existe"
logger = logging.getLogger(__name__)


def _opciones_detalle() -> tuple:
    """Cliente (a uno) con joinedload; renglones (colección) con selectinload y el libro
    de cada renglón con joinedload dentro del selectinload: 2 consultas fijas.
    Es una función para no configurar los mappers al importar el módulo."""
    return (
        joinedload(Venta.cliente),
        selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
    )


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
    """Mapea una venta con cliente y renglones (con libro) ya precargados."""
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


async def crear_venta(session: SessionDep, datos: VentaCreate) -> VentaRead:
    """Crea la venta con sus renglones en una única transacción.

    El DTO ya validó renglones (no vacío, sin libro repetido, cantidad > 0). Los
    precios se leen de la base en una sola consulta (RN-06); eso es lo que permite
    detectar un libro inexistente. El cliente no se consulta: lo rechaza la FK.
    """
    ids = [r.libro_id for r in datos.renglones]
    resultado = await session.exec(select(Libro).where(Libro.id.in_(ids)))
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
    session.add(venta)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=409, detail=MENSAJE_REFERENCIA_INVALIDA)
    return await obtener_venta(session, venta.id)


async def listar_ventas(
    session: SessionDep, pag: Paginacion, cliente_id: int | None = None
) -> list[VentaRead]:
    consulta = select(Venta).options(*_opciones_detalle())
    if cliente_id is not None:
        consulta = consulta.where(Venta.cliente_id == cliente_id)
    resultado = await session.exec(
        consulta.order_by(Venta.id).offset(pag.offset).limit(pag.limit)
    )
    return [_a_venta_read(v) for v in resultado.all()]


async def obtener_venta(session: SessionDep, id: int) -> VentaRead:
    resultado = await session.exec(
        select(Venta)
        .where(Venta.id == id)
        .options(*_opciones_detalle())
        .execution_options(populate_existing=True)
    )
    venta = resultado.first()
    if venta is None:
        raise HTTPException(status_code=404, detail=MENSAJE_VENTA_NO_ENCONTRADA)
    return _a_venta_read(venta)
