"""Motor asincrónico, fábrica de sesiones y dependencia de sesión por petición."""

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import Settings


def crear_motor(settings: Settings) -> AsyncEngine:
    """Crea el motor asincrónico con el tamaño de pool declarado en Settings."""
    return create_async_engine(
        settings.database_url,
        echo=settings.SQL_ECHO,
        pool_size=settings.DB_POOL_SIZE,
    )


def crear_fabrica_sesiones(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Una sesión por petición; se cierra siempre. Sin commit automático."""
    async with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
