"""Utilidades compartidas por el arnés de pruebas de C-13.

Fija las variables de entorno de la aplicación ANTES de importar `app.*` y
ofrece helpers para crear datos y consultar la base de prueba.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

import bcrypt
import httpx
from sqlalchemy import text

RAIZ = Path(__file__).resolve().parents[1]
BASE = "libreria_test"


def _password_postgres() -> str:
    """Lee la clave de PostgreSQL del entorno o del pgpass local (nunca del repo)."""
    if "POSTGRES_PASSWORD" in os.environ:
        return os.environ["POSTGRES_PASSWORD"]
    pgpass = Path(os.environ.get("APPDATA", "")) / "postgresql" / "pgpass.conf"
    if pgpass.exists():
        for linea in pgpass.read_text(encoding="utf-8").splitlines():
            partes = linea.strip().split(":")
            if len(partes) >= 5 and partes[3] == "postgres":
                return partes[4]
    return ""


CONEXION = {
    "user": os.environ.get("POSTGRES_USER", "postgres"),
    "password": _password_postgres(),
    "host": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
    "port": int(os.environ.get("POSTGRES_PORT", "5432")),
}

_VARIABLES = {
    "POSTGRES_USER": CONEXION["user"],
    "POSTGRES_PASSWORD": CONEXION["password"],
    "POSTGRES_DB": BASE,
    "POSTGRES_HOST": CONEXION["host"],
    "POSTGRES_PORT": str(CONEXION["port"]),
    "JWT_SECRET_KEY": "clave-de-prueba-no-secreta",
    "BCRYPT_COST": "4",
    "BCRYPT_CONCURRENCIA": "4",
    "COOKIE_SECURE": "false",
    "SQL_ECHO": "false",
}
os.environ.update(_VARIABLES)


def entorno() -> dict[str, str]:
    return os.environ.copy()


async def recrear_base() -> None:
    import asyncpg

    conexion = await asyncpg.connect(database="postgres", **CONEXION)
    try:
        await conexion.execute(f'DROP DATABASE IF EXISTS "{BASE}" WITH (FORCE)')
        await conexion.execute(f'CREATE DATABASE "{BASE}"')
    finally:
        await conexion.close()


def _tablas() -> list[str]:
    import app.models  # noqa: F401  (registra todos los mappers)
    from sqlmodel import SQLModel

    return [tabla.name for tabla in SQLModel.metadata.sorted_tables]


async def truncar() -> None:
    import asyncpg

    conexion = await asyncpg.connect(database=BASE, **CONEXION)
    try:
        tablas = ", ".join(f'"{tabla}"' for tabla in _tablas())
        await conexion.execute(f"TRUNCATE TABLE {tablas} RESTART IDENTITY CASCADE")
    finally:
        await conexion.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8")


async def crear_usuario(
    fabrica,
    *,
    email: str,
    password: str,
    rol: str,
    nombre: str | None = None,
    con_cliente: bool = False,
):
    from app.modules.clientes.models import Cliente
    from app.modules.usuarios.models import AsignacionRol, Usuario

    async with fabrica() as sesion:
        usuario = Usuario(
            email=email,
            nombre=nombre or email,
            password_hash=hash_password(password),
        )
        sesion.add(usuario)
        await sesion.flush()
        sesion.add(AsignacionRol(usuario_id=usuario.id, rol=rol))
        ficha = None
        if con_cliente:
            ficha = Cliente(nombre=nombre or email, email=email, usuario_id=usuario.id)
            sesion.add(ficha)
            await sesion.flush()
        await sesion.commit()
        return {"usuario_id": usuario.id, "cliente_id": ficha.id if ficha else None}


async def crear_catalogo(fabrica):
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero

    async with fabrica() as sesion:
        editorial = Editorial(nombre="Sudamericana", pais="Argentina")
        genero = Genero(nombre="Novela")
        autor = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")
        sesion.add_all([editorial, genero, autor])
        await sesion.commit()
        return {
            "editorial_id": editorial.id,
            "genero_id": genero.id,
            "autor_id": autor.id,
        }


async def token(cliente: httpx.AsyncClient, email: str, password: str) -> str:
    respuesta = await cliente.post(
        "/auth/login", json={"email": email, "password": password}
    )
    assert respuesta.status_code == 200, respuesta.text
    return respuesta.cookies["access_token"]


def sesion(cliente: httpx.AsyncClient, token_acceso: str) -> None:
    """Deja el cliente HTTP con una sola cookie de sesión (la indicada)."""
    cliente.cookies.clear()
    cliente.cookies.set("access_token", token_acceso)


async def fetch(fabrica, sql: str, **parametros):
    async with fabrica() as sesion:
        resultado = await sesion.exec(text(sql), params=parametros)
        return [dict(fila) for fila in resultado.mappings().all()]


async def crear_libro(cliente, token_admin, catalogo, **cambios):
    datos = {
        "isbn": "978-950-01",
        "titulo": "Rayuela",
        "precio": "1500.00",
        "stock_inicial": 4,
        "editorial_id": catalogo["editorial_id"],
        "genero_id": catalogo["genero_id"],
        "autores": [{"autor_id": catalogo["autor_id"], "rol": "autor", "orden": 1}],
    }
    datos.update(cambios)
    sesion(cliente, token_admin)
    return await cliente.post("/libros/", json=datos)


async def vender(cliente, token_personal, cliente_id: int, renglones: list[dict]):
    sesion(cliente, token_personal)
    return await cliente.post(
        "/ventas/", json={"cliente_id": cliente_id, "renglones": renglones}
    )


def assert_invariante_stock(movimientos: list[dict], libros: list[dict]) -> None:
    """Cada libro tiene stock == suma de las cantidades de sus movimientos."""
    sumas: dict[int, int] = {}
    for movimiento in movimientos:
        sumas[movimiento["libro_id"]] = sumas.get(movimiento["libro_id"], 0) + movimiento["cantidad"]
    for libro in libros:
        assert libro["stock"] == sumas.get(libro["id"], 0), libro


@asynccontextmanager
async def contar_consultas(engine):
    """Cuenta las sentencias SQL emitidas por el motor mientras dura el bloque."""
    from sqlalchemy import event

    consultas: list[str] = []

    def _antes(conn, cursor, statement, parameters, context, executemany):
        consultas.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", _antes)
    try:
        yield consultas
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", _antes)
