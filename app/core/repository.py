"""Repositorios base genéricos sobre SQLModel con sesiones async."""

from datetime import UTC, datetime
from typing import TypeVar, Type

from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel, select

T = TypeVar("T", bound=SQLModel)


class BaseRepository[T]:
    """Repositorio genérico de solo lectura/escritura sin transacción."""

    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        self.session = session
        self.model_cls = model_cls

    async def get_by_id(self, id: int) -> T | None:
        statement = select(self.model_cls).where(self.model_cls.id == id)
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        statement = select(self.model_cls).offset(offset).limit(limit)
        result = await self.session.exec(statement)
        return result.all()

    async def count(self) -> int:
        statement = select(func.count()).select_from(self.model_cls)
        result = await self.session.exec(statement)
        return result.one()

    async def add(self, instance: T) -> T:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T) -> T:
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        self.session.delete(instance)
        await self.session.flush()


class SoftDeleteRepository[T](BaseRepository[T]):
    """Repositorio con soft-delete: filtra borrado_en IS NULL por defecto."""

    def __init__(self, session: AsyncSession, model_cls: Type[T]):
        super().__init__(session, model_cls)

    def _no_deleted_filter(self):
        return self.model_cls.borrado_en.is_(None)

    async def get_by_id(self, id: int) -> T | None:
        statement = (
            select(self.model_cls)
            .where(self.model_cls.id == id)
            .where(self._no_deleted_filter())
        )
        result = await self.session.exec(statement)
        return result.first()

    async def get_all(self, offset: int = 0, limit: int = 100) -> list[T]:
        statement = (
            select(self.model_cls)
            .where(self._no_deleted_filter())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.exec(statement)
        return result.all()

    async def count(self) -> int:
        statement = (
            select(func.count())
            .select_from(self.model_cls)
            .where(self._no_deleted_filter())
        )
        result = await self.session.exec(statement)
        return result.one()

    async def get_by_id_including_deleted(self, id: int) -> T | None:
        statement = select(self.model_cls).where(self.model_cls.id == id)
        result = await self.session.exec(statement)
        return result.first()

    async def soft_delete(self, instance: T) -> T:
        instance.borrado_en = datetime.now(UTC)
        await self.session.flush()
        return instance
