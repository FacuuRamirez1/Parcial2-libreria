"""Repositorio del módulo generos.

Solo métodos genéricos de BaseRepository; escritura por flush() (el commit es
responsabilidad del UnitOfWork).
"""

from app.core.repository import BaseRepository
from app.modules.generos.models import Genero


class GeneroRepository(BaseRepository[Genero]):
    pass
