"""Repositorio del módulo libros.

Métodos genéricos de BaseRepository más búsqueda filtrada por título y género,
con precarga de editorial y género declarada dentro de los métodos de listado
y detalle. Sin borrado_en ni soft_delete (esa columna no existe en C-09).
"""

from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlmodel import SQLModel

from app.core.repository import BaseRepository
from app.modules.libros.models import Libro


class LibroRepository(BaseRepository[Libro]):
    """Acceso a Libro con filtros de catálogo y carga anticipada."""

    def _opciones_lista(self) -> tuple:
        return (joinedload(Libro.editorial), joinedload(Libro.genero))

    async def get_all_filtrado(
        self,
        titulo: str | None = None,
        genero_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Libro]:
        """Lista de libros filtrada por título (ILIKE ligado) y género opcional."""
        consulta = select(Libro).options(*self._opciones_lista())
        if titulo:
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        resultado = await self.session.exec(
            consulta.order_by(Libro.id).offset(offset).limit(limit)
        )
        return resultado.all()

    async def count_filtrado(
        self, titulo: str | None = None, genero_id: int | None = None
    ) -> int:
        """Conteo coherente con los mismos filtros de get_all_filtrado."""
        consulta = select(func.count()).select_from(Libro)
        if titulo:
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        resultado = await self.session.exec(consulta)
        return resultado.one()
