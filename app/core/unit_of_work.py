"""Unit of Work base: gestor de contexto asincrónico para agrupar escrituras.

Confirma al salir del bloque sin excepción y revierte ante excepción. No cierra
la sesión porque no la creó (quien la creó, get_session, es la responsable).
"""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class UnitOfWork:
    """Agrupa varias escrituras en una sola transacción sobre una sesión."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self) -> "UnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()
