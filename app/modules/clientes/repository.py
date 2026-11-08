"""Repositorio del módulo clientes.

Métodos genéricos de BaseRepository más búsqueda por email; escritura por
flush() (el commit es responsabilidad del UnitOfWork).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.clientes.models import Cliente


class ClienteRepository(BaseRepository[Cliente]):

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Cliente)

    async def get_by_email(self, email: str) -> Cliente | None:
        from sqlmodel import select

        resultado = await self.session.exec(
            select(Cliente).where(Cliente.email == email)
        )
        return resultado.first()
