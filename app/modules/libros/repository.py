"""Repositorio del módulo libros.

`LibroRepository` hereda de `SoftDeleteRepository`: las lecturas excluyen los
libros dados de baja y el detalle conserva la precarga declarada en el método.
`MovimientoStockRepository` lista el historial de un libro (solo agregado).
"""

from typing import Sequence

from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.orm import joinedload, selectinload

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository, SoftDeleteRepository
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock


class LibroRepository(SoftDeleteRepository[Libro]):
    """Acceso a Libro con filtros de catálogo, baja lógica y carga anticipada."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Libro)

    def _opciones_lista(self) -> tuple:
        return (joinedload(Libro.editorial), joinedload(Libro.genero))

    def _opciones_detalle(self) -> tuple:
        return (
            *self._opciones_lista(),
            selectinload(Libro.autorias).joinedload(LibroAutor.autor),
        )

    async def get_detalle(self, id: int) -> Libro | None:
        """Libro vigente con editorial, género y autorías precargados."""
        resultado = await self.session.exec(
            select(Libro)
            .where(Libro.id == id)
            .where(Libro.borrado_en.is_(None))
            .options(*self._opciones_detalle())
            .execution_options(populate_existing=True)
        )
        return resultado.first()

    async def get_all_filtrado(
        self,
        titulo: str | None = None,
        genero_id: int | None = None,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> Sequence[Libro]:
        """Lista de libros vigentes filtrada por título (ILIKE ligado) y género opcional."""
        consulta = (
            select(Libro)
            .where(Libro.borrado_en.is_(None))
            .options(*self._opciones_lista())
        )
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
        """Conteo de libros vigentes con los mismos filtros de get_all_filtrado."""
        consulta = select(func.count()).select_from(Libro).where(Libro.borrado_en.is_(None))
        if titulo:
            consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
        if genero_id is not None:
            consulta = consulta.where(Libro.genero_id == genero_id)
        resultado = await self.session.exec(consulta)
        return resultado.one()


class MovimientoStockRepository(BaseRepository[MovimientoStock]):
    """Lecturas del historial de movimientos (nunca escribe: es solo agregado)."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MovimientoStock)

    async def listar_de_libro(self, libro_id: int) -> list[MovimientoStock]:
        resultado = await self.session.exec(
            select(MovimientoStock)
            .where(MovimientoStock.libro_id == libro_id)
            .order_by(MovimientoStock.id)
        )
        return list(resultado.all())
