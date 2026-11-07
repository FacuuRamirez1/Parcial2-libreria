"""Carga datos iniciales de los casos C-01 a C-08.

El esquema se crea únicamente con Alembic (`alembic upgrade head`). Este script
lee `DATABASE_URL` del entorno o del `.env`, y es idempotente: si ya hay libros,
no vuelve a cargar nada.
"""

from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.modules.autores.models import Autor  # noqa: E402
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor  # noqa: E402
from app.modules.usuarios.models import Usuario  # noqa: E402,F401
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402


def _agregar(sesion: AsyncSession, *objetos: object) -> None:
    for objeto in objetos:
        sesion.add(objeto)


async def cargar_datos(sesion: AsyncSession) -> bool:
    """Carga el catálogo si la base está vacía. Devuelve False si ya había datos."""
    cantidad = (
        await sesion.exec(select(func.count()).select_from(Libro))
    ).one()
    if cantidad:
        print(f"Seed omitido: ya hay {cantidad} libros cargados.")
        return False

    sudamericana = Editorial(nombre="Sudamericana", pais="Argentina")
    anagrama = Editorial(nombre="Anagrama", pais="España")
    emece = Editorial(nombre="Emecé", pais="Argentina")
    _agregar(sesion, sudamericana, anagrama, emece)

    novela = Genero(nombre="Novela")
    cuento = Genero(nombre="Cuento")
    ensayo = Genero(nombre="Ensayo")
    _agregar(sesion, novela, cuento, ensayo)

    cortazar = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")
    garcia_marquez = Autor(nombre="Gabriel García Márquez", nacionalidad="Colombia")
    schweblin = Autor(nombre="Samanta Schweblin", nacionalidad="Argentina")
    enriquez = Autor(nombre="Mariana Enríquez", nacionalidad="Argentina")
    _agregar(sesion, cortazar, garcia_marquez, schweblin, enriquez)
    await sesion.flush()

    rayuela = Libro(
        isbn="978-84-376-0494-7",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=12,
        editorial_id=sudamericana.id,
        genero_id=novela.id,
    )
    cien_anios = Libro(
        isbn="978-84-397-3459-8",
        titulo="Cien años de soledad",
        precio=Decimal("30000.00"),
        stock=8,
        editorial_id=sudamericana.id,
        genero_id=novela.id,
    )
    distancia = Libro(
        isbn="978-84-339-7936-2",
        titulo="Distancia de rescate",
        precio=Decimal("18000.00"),
        stock=15,
        editorial_id=anagrama.id,
        genero_id=novela.id,
    )
    fuego = Libro(
        isbn="978-84-339-7899-9",
        titulo="Las cosas que perdimos en el fuego",
        precio=Decimal("22000.00"),
        stock=6,
        editorial_id=anagrama.id,
        genero_id=cuento.id,
    )
    _agregar(sesion, rayuela, cien_anios, distancia, fuego)
    await sesion.flush()

    _agregar(
        sesion,
        LibroAutor(libro_id=rayuela.id, autor_id=cortazar.id, rol="autor", orden=1),
        LibroAutor(
            libro_id=cien_anios.id,
            autor_id=garcia_marquez.id,
            rol="autor",
            orden=1,
        ),
        LibroAutor(
            libro_id=distancia.id, autor_id=schweblin.id, rol="autor", orden=1
        ),
        LibroAutor(libro_id=fuego.id, autor_id=enriquez.id, rol="autor", orden=1),
        LibroAutor(libro_id=fuego.id, autor_id=schweblin.id, rol="coautor", orden=2),
    )

    tomas = Cliente(nombre="Tomás Ríos", email="tomas.rios@example.com")
    ana = Cliente(nombre="Ana Pérez", email="ana.perez@example.com")
    _agregar(sesion, tomas, ana)
    await sesion.flush()

    _agregar(
        sesion,
        PerfilCliente(
            cliente_id=tomas.id,
            telefono="11-5555-0101",
            direccion="Av. Corrientes 1234",
        ),
    )

    venta = Venta(cliente_id=tomas.id, total=Decimal("61000.00"))
    _agregar(sesion, venta)
    await sesion.flush()
    _agregar(
        sesion,
        RenglonVenta(
            venta_id=venta.id,
            libro_id=rayuela.id,
            cantidad=1,
            precio_unitario=rayuela.precio,
        ),
        RenglonVenta(
            venta_id=venta.id,
            libro_id=distancia.id,
            cantidad=2,
            precio_unitario=distancia.precio,
        ),
    )

    await sesion.commit()
    print(
        "Seed completado: 3 editoriales, 3 géneros, 4 autores, 4 libros, "
        "2 clientes y 1 venta con 2 renglones."
    )
    return True


async def main() -> None:
    load_dotenv(RAIZ / ".env", override=False)
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        raise SystemExit(
            "Falta DATABASE_URL (defínela en el entorno o en el archivo .env)."
        )

    engine = create_async_engine(url, echo=False)
    try:
        fabrica = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with fabrica() as sesion:
            await cargar_datos(sesion)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
