"""Script temporal de setup de base para pruebas de C-04 (no es código de la app)."""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

import app.models  # noqa: F401  registra todas las tablas


async def main() -> None:
    engine = create_async_engine("postgresql+asyncpg://postgres@localhost:5433/legado_arbitral")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    await engine.dispose()
    print("Tablas creadas")


asyncio.run(main())
