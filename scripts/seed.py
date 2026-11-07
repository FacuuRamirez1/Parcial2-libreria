"""Carga el estado inicial conocido para los casos C-01 a C-08.

El esquema se crea únicamente con Alembic (`alembic upgrade head`). Este script
lee `DATABASE_URL` del entorno o del `.env`, y es idempotente: si ya hay libros,
no vuelve a cargar nada.

Ids resultantes (base vacía): editoriales 1-3, géneros 1-3, autores 1-6, libros 1-4,
clientes 1-2 y una venta (id 1) del cliente 1. El cliente 1 ya tiene perfil y el
cliente 2 no; los libros 1 y 4 cuestan 25000.00 y 27000.00, como en la consigna.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.core.config import Settings  # noqa: E402
from app.modules.autores.models import Autor  # noqa: E402
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor  # noqa: E402
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402


async def cargar_datos(sesion: AsyncSession) -> bool:
    """Carga el catálogo si la base está vacía. Devuelve False si ya había datos."""
    cantidad = (await sesion.exec(select(func.count()).select_from(Libro))).one()
    if cantidad:
        print(f"Seed omitido: ya hay {cantidad} libros cargados.")
        return False

    sudamericana = Editorial(nombre="Sudamericana", pais="Argentina")
    anagrama = Editorial(nombre="Anagrama", pais="España")
    emece = Editorial(nombre="Emecé", pais="Argentina")
    sesion.add_all([sudamericana, anagrama, emece])

    novela = Genero(nombre="Novela")
    cuento = Genero(nombre="Cuento")
    ensayo = Genero(nombre="Ensayo")
    sesion.add_all([novela, cuento, ensayo])

    cortazar = Autor(nombre="Julio Cortázar", nacionalidad="Argentina")
    garcia_marquez = Autor(nombre="Gabriel García Márquez", nacionalidad="Colombia")
    bioy = Autor(nombre="Adolfo Bioy Casares", nacionalidad="Argentina")
    ocampo = Autor(nombre="Silvina Ocampo", nacionalidad="Argentina")
    piglia = Autor(nombre="Ricardo Piglia", nacionalidad="Argentina")
    borges = Autor(nombre="Jorge Luis Borges", nacionalidad="Argentina")
    sesion.add_all([cortazar, garcia_marquez, bioy, ocampo, piglia, borges])
    await sesion.flush()

    # Las autorías se crean con ids explícitos: leer `libro.autorias` dispararía una
    # carga perezosa, que está prohibida (lazy="raise").
    rayuela = Libro(
        isbn="978-950-00-0001-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=12,
        editorial_id=sudamericana.id,
        genero_id=novela.id,
    )
    cien_anios = Libro(
        isbn="978-950-00-0002-8",
        titulo="Cien años de soledad",
        precio=Decimal("30000.00"),
        stock=8,
        editorial_id=sudamericana.id,
        genero_id=novela.id,
    )
    antologia = Libro(
        isbn="978-950-00-0003-5",
        titulo="Antología de la literatura fantástica",
        precio=Decimal("22000.00"),
        stock=6,
        editorial_id=emece.id,
        genero_id=cuento.id,
    )
    respiracion = Libro(
        isbn="978-950-00-0004-2",
        titulo="Respiración artificial",
        precio=Decimal("27000.00"),
        stock=15,
        editorial_id=anagrama.id,
        genero_id=novela.id,
    )
    sesion.add_all([rayuela, cien_anios, antologia, respiracion])
    await sesion.flush()

    sesion.add_all(
        [
            LibroAutor(libro_id=rayuela.id, autor_id=cortazar.id, rol="autor", orden=1),
            LibroAutor(
                libro_id=cien_anios.id, autor_id=garcia_marquez.id, rol="autor", orden=1
            ),
            # Libro con varios autores: sirve para comprobar el detalle sin N+1.
            LibroAutor(libro_id=antologia.id, autor_id=borges.id, rol="coautor", orden=1),
            LibroAutor(libro_id=antologia.id, autor_id=ocampo.id, rol="coautor", orden=2),
            LibroAutor(libro_id=antologia.id, autor_id=bioy.id, rol="coautor", orden=3),
            LibroAutor(
                libro_id=respiracion.id, autor_id=piglia.id, rol="autor", orden=1
            ),
        ]
    )

    ana = Cliente(nombre="Ana Pérez", email="ana.perez@example.com")
    tomas = Cliente(nombre="Tomás Ríos", email="tomas@example.com")
    sesion.add_all([ana, tomas])
    await sesion.flush()

    sesion.add(
        PerfilCliente(
            cliente_id=ana.id, telefono="11-5555-0101", direccion="Av. Corrientes 1234"
        )
    )

    venta = Venta(cliente_id=ana.id, total=Decimal("79000.00"))
    sesion.add(venta)
    await sesion.flush()
    sesion.add_all(
        [
            RenglonVenta(
                venta_id=venta.id,
                libro_id=rayuela.id,
                cantidad=1,
                precio_unitario=rayuela.precio,
            ),
            RenglonVenta(
                venta_id=venta.id,
                libro_id=respiracion.id,
                cantidad=2,
                precio_unitario=respiracion.precio,
            ),
        ]
    )

    await sesion.commit()
    print(
        "Seed completado: 3 editoriales, 3 géneros, 6 autores, 4 libros, "
        "2 clientes (uno con perfil) y 1 venta con 2 renglones."
    )
    return True


async def main() -> None:
    url = Settings().database_url
    engine = create_async_engine(url, echo=False)
    try:
        fabrica = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with fabrica() as sesion:
            await cargar_datos(sesion)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
