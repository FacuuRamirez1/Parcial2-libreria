"""Repositorio del módulo ventas.

Métodos genéricos de BaseRepository más el detalle con precarga fija (sin N+1)
y filtrado opcional por cliente; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from typing import Sequence

from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.orm import joinedload, selectinload

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.ventas.models import RenglonVenta, Venta


class VentaRepository(BaseRepository[Venta]):
    """Acceso a Venta con detalle precargado y filtro opcional por cliente."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Venta)


    def _opciones_detalle(self) -> tuple:
        return (
            joinedload(Venta.cliente),
            selectinload(Venta.renglones).joinedload(RenglonVenta.libro),
        )

    async def get_con_detalle(self, id: int) -> Venta | None:
        """Venta por id con cliente y renglones → libro precargados (2 consultas fijas)."""
        resultado = await self.session.exec(
            select(Venta)
            .where(Venta.id == id)
            .options(*self._opciones_detalle())
            .execution_options(populate_existing=True)
        )
        return resultado.first()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        cliente_id: int | None = None,
    ) -> Sequence[Venta]:
        """Listado de ventas con precarga de detalle y filtro opcional por cliente."""
        consulta = select(Venta).options(*self._opciones_detalle())
        if cliente_id is not None:
            consulta = consulta.where(Venta.cliente_id == cliente_id)
        resultado = await self.session.exec(
            consulta.order_by(Venta.id).offset(offset).limit(limit)
        )
        return resultado.all()

    async def count(self, *, cliente_id: int | None = None) -> int:
        """Conteo de ventas con el mismo filtro opcional por cliente."""
        consulta = select(func.count()).select_from(Venta)
        if cliente_id is not None:
            consulta = consulta.where(Venta.cliente_id == cliente_id)
        resultado = await self.session.exec(consulta)
        return resultado.one()
