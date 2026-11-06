"""Configuración de la suite de pruebas: PostgreSQL real y esquema vía Alembic.

La suite requiere `TEST_DATABASE_URL` (o `DATABASE_URL` como respaldo) apuntando a
una base PostgreSQL 16 con el driver `postgresql+asyncpg`. El esquema se crea con
`alembic upgrade head` de forma programática; nunca con `create_all`.
"""

from __future__ import annotations

import io
import logging
import os
from collections.abc import AsyncIterator, Iterator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any, Callable

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.database import get_session
from app.main import app

RAIZ = Path(__file__).resolve().parent.parent
# Permite `pytest` usando el mismo .env que la app (el entorno del proceso prevalece).
load_dotenv(RAIZ / ".env", override=False)
PREFIJO_DRIVER = "postgresql+asyncpg://"
TABLAS_SIN_LIMPIAR = {"alembic_version"}


def _url_prueba() -> str:
    """Devuelve la URL de la base de prueba y valida el driver asincrónico."""
    url = os.environ.get("TEST_DATABASE_URL", "").strip()
    if not url:
        url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise pytest.UsageError(
            "Definí TEST_DATABASE_URL (o DATABASE_URL) para ejecutar la suite."
        )
    if not url.startswith(PREFIJO_DRIVER):
        raise pytest.UsageError(
            "TEST_DATABASE_URL debe usar el driver asincrónico postgresql+asyncpg."
        )
    return url


@contextmanager
def _database_url_de_migraciones(url: str) -> Iterator[None]:
    """Publica temporalmente la URL de prueba como DATABASE_URL para Alembic."""
    anterior = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        yield
    finally:
        if anterior is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = anterior


def _aplicar_migraciones(url: str) -> None:
    """Aplica `alembic upgrade head` una vez por sesión, sin ruido en consola."""
    config = Config(str(RAIZ / "alembic.ini"), output_buffer=io.StringIO())
    # Alembic 1.20 resuelve `script_location` de forma perezosa desde el .ini:
    # anular `config_file_name` sin fijarlo antes rompe `upgrade`.
    config.set_main_option("script_location", str(RAIZ / "migrations"))
    # Evita que env.py reconfigǧre el logging con el logging.config del .ini.
    config.config_file_name = None
    logging.getLogger("alembic").setLevel(logging.CRITICAL)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.CRITICAL)
    buffer = io.StringIO()
    with _database_url_de_migraciones(url):
        with redirect_stdout(buffer), redirect_stderr(buffer):
            command.upgrade(config, "head")


@pytest.fixture(scope="session")
def engine() -> Iterator[AsyncEngine]:
    """Motor de prueba con NullPool para no atar conexiones a un event loop."""
    motor = create_async_engine(_url_prueba(), echo=False, poolclass=NullPool)
    try:
        yield motor
    finally:
        import asyncio

        asyncio.run(motor.dispose())


@pytest.fixture(scope="session")
def fabrica_sesiones(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Fábrica de sesiones de prueba equivalente a la de la app."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def preparar_base() -> None:
    """Crea el esquema una única vez; la base de prueba también usa Alembic."""
    _aplicar_migraciones(_url_prueba())


@pytest.fixture(scope="session", autouse=True)
def sobrescribir_sesion(
    fabrica_sesiones: async_sessionmaker[AsyncSession],
) -> Iterator[None]:
    """Sobrescribe `get_session` para que la app use la base de prueba."""

    async def _sesion_prueba() -> AsyncIterator[AsyncSession]:
        async with fabrica_sesiones() as sesion:
            yield sesion

    app.dependency_overrides[get_session] = _sesion_prueba
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_session, None)


@pytest_asyncio.fixture(autouse=True)
async def limpiar_base(
    engine: AsyncEngine, preparar_base: None
) -> AsyncIterator[None]:
    """Deja las tablas de dominio vacías antes de cada test (sin tocar Alembic)."""
    async with engine.begin() as conexion:
        resultado = await conexion.execute(
            text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        )
        tablas = [fila for fila in resultado.scalars().all() if fila not in TABLAS_SIN_LIMPIAR]
        if tablas:
            lista = ", ".join('"' + tabla.replace('"', '""') + '"' for tabla in tablas)
            await conexion.execute(text(f"TRUNCATE {lista} RESTART IDENTITY CASCADE"))
    yield


@pytest_asyncio.fixture
async def sesion(
    fabrica_sesiones: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Sesión directa contra la base de prueba para inspecciones."""
    async with fabrica_sesiones() as sesion_prueba:
        yield sesion_prueba


@pytest_asyncio.fixture
async def cliente_http(sobrescribir_sesion: None) -> AsyncIterator[AsyncClient]:
    """Cliente HTTP sobre la app ASGI, sin depender del lifespan."""
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://test") as cliente:
        yield cliente


@pytest_asyncio.fixture
async def editorial(cliente_http: AsyncClient) -> dict[str, Any]:
    """Crea una editorial por la API y devuelve su representación."""
    respuesta = await cliente_http.post(
        "/editoriales/", json={"nombre": "Editorial de Prueba", "pais": "Argentina"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


@pytest_asyncio.fixture
async def genero(cliente_http: AsyncClient) -> dict[str, Any]:
    """Crea un género por la API y devuelve su representación."""
    respuesta = await cliente_http.post(
        "/generos/", json={"nombre": "Género de Prueba"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


@pytest_asyncio.fixture
async def autor(cliente_http: AsyncClient) -> dict[str, Any]:
    """Crea un autor por la API y devuelve su representación."""
    respuesta = await cliente_http.post(
        "/autores/", json={"nombre": "Autor de Prueba", "nacionalidad": "Argentina"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


@pytest_asyncio.fixture
async def cliente(cliente_http: AsyncClient) -> dict[str, Any]:
    """Crea un cliente por la API y devuelve su representación."""
    respuesta = await cliente_http.post(
        "/clientes/",
        json={"nombre": "Cliente de Prueba", "email": "cliente.prueba@example.com"},
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


@pytest.fixture
def crear_libro(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
) -> Callable[..., Any]:
    """Devuelve una función para crear libros válidos, ajustando campos."""

    async def _crear(**cambios: Any) -> dict[str, Any]:
        datos: dict[str, Any] = {
            "isbn": "978-84-376-0494-7",
            "titulo": "Libro de Prueba",
            "precio": "25.00",
            "stock_inicial": 10,
            "editorial_id": editorial["id"],
            "genero_id": genero["id"],
        }
        datos.update(cambios)
        respuesta = await cliente_http.post("/libros/", json=datos)
        assert respuesta.status_code == 201, respuesta.text
        return respuesta.json()

    return _crear


@pytest_asyncio.fixture
async def libro(crear_libro: Callable[..., Any]) -> dict[str, Any]:
    """Crea un libro válido con una editorial y un género de prueba."""
    return await crear_libro()
