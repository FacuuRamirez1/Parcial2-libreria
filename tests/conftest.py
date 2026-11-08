"""Arnés de pruebas de C-13: PostgreSQL de prueba migrado con Alembic."""

from __future__ import annotations

import asyncio
import subprocess
import sys

import httpx
import pytest
import pytest_asyncio

from tests import ayuda


@pytest.fixture(scope="session", autouse=True)
def base_migrada():
    """Recrea la base de prueba y la deja en `head` una sola vez por sesión."""
    asyncio.run(ayuda.recrear_base())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=ayuda.RAIZ,
        env=ayuda.entorno(),
        check=True,
    )
    yield


@pytest_asyncio.fixture(autouse=True)
async def base_limpia(base_migrada):
    """Cada prueba arranca con las tablas vacías (TRUNCATE no dispara el trigger)."""
    await ayuda.truncar()
    yield


@pytest_asyncio.fixture
async def cliente():
    """Cliente HTTP contra la app real, con su lifespan (motor, semáforo, hash)."""
    from app.main import app

    async with app.router.lifespan_context(app):
        transporte = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://prueba") as http:
            http.app = app
            yield http


@pytest_asyncio.fixture
async def fabrica(cliente):
    return cliente.app.state.session_factory


@pytest_asyncio.fixture
async def usuarios(fabrica):
    admin = await ayuda.crear_usuario(
        fabrica, email="admin@example.com", password="admin1234", rol="ADMIN", nombre="Admin"
    )
    vendedor = await ayuda.crear_usuario(
        fabrica, email="vendedor@example.com", password="vende1234", rol="VENDEDOR", nombre="Vendedor"
    )
    ana = await ayuda.crear_usuario(
        fabrica,
        email="ana@example.com",
        password="ana12345",
        rol="CLIENTE",
        nombre="Ana Paz",
        con_cliente=True,
    )
    otro = await ayuda.crear_usuario(
        fabrica,
        email="otro@example.com",
        password="otro1234",
        rol="CLIENTE",
        nombre="Otro Cliente",
        con_cliente=True,
    )
    return {"admin": admin, "vendedor": vendedor, "ana": ana, "otro": otro}


@pytest_asyncio.fixture
async def catalogo(fabrica):
    return await ayuda.crear_catalogo(fabrica)


@pytest_asyncio.fixture
async def sesiones(cliente, usuarios):
    return {
        "admin": await ayuda.token(cliente, "admin@example.com", "admin1234"),
        "vendedor": await ayuda.token(cliente, "vendedor@example.com", "vende1234"),
        "ana": await ayuda.token(cliente, "ana@example.com", "ana12345"),
        "otro": await ayuda.token(cliente, "otro@example.com", "otro1234"),
    }
