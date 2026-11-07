"""Pruebas del script de datos iniciales (C-07)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import func
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.ventas.models import RenglonVenta, Venta

RAIZ = Path(__file__).resolve().parent.parent


def _url_de_prueba() -> str:
    return os.environ.get("TEST_DATABASE_URL") or os.environ["DATABASE_URL"]


def _ejecutar_seed() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "seed.py")],
        cwd=RAIZ,
        env={**os.environ, "DATABASE_URL": _url_de_prueba()},
        capture_output=True,
        text=True,
        timeout=60,
    )


async def _conteos(sesion: AsyncSession) -> dict[str, Any]:
    async def contar(modelo: Any) -> int:
        resultado = await sesion.exec(select(func.count()).select_from(modelo))
        return resultado.one()

    return {
        "editoriales": await contar(Editorial),
        "generos": await contar(Genero),
        "autores": await contar(Autor),
        "libros": await contar(Libro),
        "autorias": await contar(LibroAutor),
        "clientes": await contar(Cliente),
        "perfiles": await contar(PerfilCliente),
        "ventas": await contar(Venta),
        "renglones": await contar(RenglonVenta),
    }


async def test_seed_carga_catalogo_y_es_idempotente(sesion: AsyncSession) -> None:
    primero = _ejecutar_seed()
    assert primero.returncode == 0, primero.stderr

    esperado = {
        "editoriales": 3,
        "generos": 3,
        "autores": 4,
        "libros": 4,
        "autorias": 5,
        "clientes": 2,
        "perfiles": 1,
        "ventas": 1,
        "renglones": 2,
    }
    assert await _conteos(sesion) == esperado

    segundo = _ejecutar_seed()
    assert segundo.returncode == 0, segundo.stderr
    assert "Seed omitido" in segundo.stdout
    assert await _conteos(sesion) == esperado
