"""Repositorio del módulo autores.

Solo métodos genéricos de BaseRepository; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from app.core.repository import BaseRepository
from app.modules.autores.models import Autor


class AutorRepository(BaseRepository[Autor]):
    pass
