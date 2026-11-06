"""Repositorio específico del módulo libros con soft delete y búsqueda."""

from typing import Type

from sqlalchemy import func
from sqlmodel import select

from app.core.repository import SoftDeleteRepository
from app.modules.libros.models import Libro


class LibroRepository(SoftDeleteRepository[Libro]):
    """Repositorio de libros que filtra borrado_en IS NULL por defecto."""

    def __init__(self, session, model_cls: Type[Libro] = Libro):
        super().__init__(session, model_cls)

    def _filtros_busqueda(
        self, titulo: str | None, genero_id: int | None
    ) -> list:
        """Filtros combinables; el patrón de `ilike` viaja como parámetro ligado."""
        filtros: list = [self._no_deleted_filter()]
        if titulo:
            filtros.append(Libro.titulo.ilike(f"%{titulo}%"))
        if genero_id is not None:
            filtros.append(Libro.genero_id == genero_id)
        return filtros

    async def get_all_filtrado(
        self,
        *,
        titulo: str | None = None,
        genero_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Libro]:
        statement = (
            select(Libro)
            .where(*self._filtros_busqueda(titulo, genero_id))
            .offset(offset)
            .limit(limit)
        )
        resultado = await self.session.exec(statement)
        return resultado.all()

    async def count_filtrado(
        self, *, titulo: str | None = None, genero_id: int | None = None
    ) -> int:
        statement = (
            select(func.count())
            .select_from(Libro)
            .where(*self._filtros_busqueda(titulo, genero_id))
        )
        resultado = await self.session.exec(statement)
        return resultado.one()
