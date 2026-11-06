"""Unit of Work asíncrono para gestionar transacciones sobre una AsyncSession."""

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Gestor de contexto asíncrono que hace commit o rollback al salir.

    La sesión no se cierra aquí: quien la creó es responsable de cerrarla.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
        else:
            await self.session.commit()
        return False
