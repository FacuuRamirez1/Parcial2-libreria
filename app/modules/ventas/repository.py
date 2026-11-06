"""Repositorio específico del módulo ventas con precarga de relaciones."""

from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.ventas.models import RenglonVenta, Venta


class VentaRepository(BaseRepository[Venta]):
    """Repositorio de ventas con carga anticipada para evitar N+1."""

    def __init__(self, session, model_cls: type[Venta] = Venta):
        super().__init__(session, model_cls)

    async def get_con_detalle(self, id: int) -> Venta | None:
        """Obtiene una venta con cliente y renglones (con libro) precargados."""
        statement = (
            select(self.model_cls)
            .where(self.model_cls.id == id)
            .options(joinedload(self.model_cls.cliente))
            .options(selectinload(self.model_cls.renglones).joinedload(RenglonVenta.libro))
        )
        result = await self.session.exec(statement)
        return result.first()
