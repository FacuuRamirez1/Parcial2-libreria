"""Repositorio del módulo autores.

Solo métodos genéricos de BaseRepository; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.autores.models import Autor


class AutorRepository(BaseRepository[Autor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Autor)
