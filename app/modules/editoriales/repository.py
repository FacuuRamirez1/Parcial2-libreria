"""Repositorio del módulo editoriales.

Solo métodos genéricos de BaseRepository; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from app.core.repository import BaseRepository
from app.modules.editoriales.models import Editorial


class EditorialRepository(BaseRepository[Editorial]):
    pass
