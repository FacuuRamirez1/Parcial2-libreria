"""Repositorio específico del módulo libros con soft delete."""

from typing import Type

from app.core.repository import SoftDeleteRepository
from app.modules.libros.models import Libro


class LibroRepository(SoftDeleteRepository[Libro]):
    """Repositorio de libros que filtra borrado_en IS NULL por defecto."""

    def __init__(self, session, model_cls: Type[Libro] = Libro):
        super().__init__(session, model_cls)
