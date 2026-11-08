"""Repositorios genéricos por entidad.

BaseRepository[T] recibe la sesión y la clase del modelo (los genéricos se
borran en tiempo de ejecución). add/update hacen flush, nunca commit: la
confirmación es responsabilidad exclusiva del UnitOfWork.
SoftDeleteRepository[T] filtra borrado_en IS NULL en lecturas y agrega
get_by_id_including_deleted y soft_delete.
"""

from collections.abc import Sequence
from datetime import datetime, timezone
from typing import TypeVar

from sqlalchemy import func
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


class BaseRepository[T]:
    """Acceso genérico a una entidad sobre una sesión dada."""

    def __init__(self, session: AsyncSession, model: type[T]) -> None:
        self.session = session
        self.model = model

    async def get_by_id(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def get_all(self, *, offset: int = 0, limit: int = 20) -> Sequence[T]:
        resultado = await self.session.exec(
            select(self.model).offset(offset).limit(limit)
        )
        return resultado.all()

    async def count(self) -> int:
        resultado = await self.session.exec(
            select(func.count()).select_from(self.model)
        )
        return resultado.one()

    async def add(self, obj: T) -> None:
        self.session.add(obj)
        await self.session.flush()

    async def update(self, obj: T) -> None:
        self.session.add(obj)
        await self.session.flush()

    async def delete(self, obj: T) -> None:
        await self.session.delete(obj)
        await self.session.flush()


class SoftDeleteRepository[T](BaseRepository[T]):
    """Soft delete por borrado_en: lecturas excluyen las filas dadas de baja."""

    async def get_by_id(self, id: int) -> T | None:
        resultado = await self.session.exec(
            select(self.model)
            .where(self.model.id == id)
            .where(self.model.borrado_en.is_(None))
        )
        return resultado.first()

    async def get_all(self, *, offset: int = 0, limit: int = 20) -> Sequence[T]:
        resultado = await self.session.exec(
            select(self.model).where(self.model.borrado_en.is_(None)).offset(offset).limit(limit)
        )
        return resultado.all()

    async def count(self) -> int:
        resultado = await self.session.exec(
            select(func.count())
            .select_from(self.model)
            .where(self.model.borrado_en.is_(None))
        )
        return resultado.one()

    async def get_by_id_including_deleted(self, id: int) -> T | None:
        return await self.session.get(self.model, id)

    async def soft_delete(self, obj: T) -> None:
        obj.borrado_en = datetime.now(timezone.utc)
        self.session.add(obj)
        await self.session.flush()
