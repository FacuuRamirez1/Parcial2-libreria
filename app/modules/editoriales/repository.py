"""Repositorio del módulo editoriales.

Solo métodos genéricos de BaseRepository; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.modules.editoriales.models import Editorial


class EditorialRepository(BaseRepository[Editorial]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Editorial)
