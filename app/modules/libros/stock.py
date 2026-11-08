"""Punto ÚNICO de escritura de `libro.stock` (RN-11).

Todo cambio de stock actualiza la fila del libro y agrega su movimiento en el
mismo paso, dentro de la transacción del Unit of Work que recibe. Ninguna otra
parte de la aplicación asigna `libro.stock`.
"""

from app.core.unit_of_work import UnitOfWork
from app.modules.libros.models import Libro, MovimientoStock


async def registrar_movimiento(
    uow: UnitOfWork,
    *,
    libro: Libro,
    cantidad: int,
    motivo: str,
    usuario_id: int,
    venta_id: int | None = None,
) -> MovimientoStock:
    """Suma `cantidad` al stock y deja la fila de `movimiento_stock` (flush, sin commit)."""
    if cantidad == 0:
        raise ValueError("Un movimiento de stock no puede tener cantidad cero")

    libro.stock += cantidad
    uow.session.add(libro)

    movimiento = MovimientoStock(
        libro_id=libro.id,
        venta_id=venta_id,
        usuario_id=usuario_id,
        cantidad=cantidad,
        motivo=motivo,
    )
    uow.session.add(movimiento)
    await uow.session.flush()
    return movimiento
