"""Datos iniciales del parcial (capítulos 1 a 6).

El esquema se crea únicamente con Alembic (`alembic upgrade head`). Este script
lee la configuración de `Settings` (`.env` o variables de entorno), vacía las
tablas y vuelve a cargar el estado inicial conocido. Es idempotente: correrlo dos
veces deja exactamente el mismo estado.

Las contraseñas de abajo son de mentira y viven solo en este archivo. Los hashes
bcrypt se calculan ANTES de abrir la transacción, fuera del bucle de eventos.

Ids resultantes (base vacía, `RESTART IDENTITY`): usuarios 1-5, editoriales 1-3,
géneros 1-3, autores 1-6, libros 1-5, clientes 1-3 y la venta 1. El stock de cada
libro coincide con la suma de sus movimientos.
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

import app.models  # noqa: E402,F401  (registra todos los modelos para que los mappers resuelvan)
from app.core.config import Settings  # noqa: E402
from app.core.security import hashear_password  # noqa: E402
from app.core.unit_of_work import UnitOfWork  # noqa: E402
from app.modules.autores.models import Autor  # noqa: E402
from app.modules.clientes.models import Cliente, PerfilCliente  # noqa: E402
from app.modules.editoriales.models import Editorial  # noqa: E402
from app.modules.generos.models import Genero  # noqa: E402
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock  # noqa: E402
from app.modules.libros.stock import registrar_movimiento  # noqa: E402
from app.modules.usuarios.models import (  # noqa: E402
    AsignacionRol,
    EventoSeguridad,
    Usuario,
)
from app.modules.ventas.models import RenglonVenta, Venta  # noqa: E402

TABLAS = (
    "usuario, asignacion_rol, intento_acceso, evento_seguridad, cliente, "
    "perfil_cliente, editorial, genero, autor, libro, libro_autor, venta, "
    "renglon_venta, movimiento_stock"
)

PASSWORD_ADMIN = "clave-admin-1"
PASSWORD_ADMIN2 = "clave-admin-2"
PASSWORD_VENDEDOR = "clave-vendedor-1"
PASSWORD_ANA = "clave-ana-1"
PASSWORD_NUEVO = "clave-nuevo-1"


async def _hashes(settings: Settings) -> dict[str, str]:
    """Calcula los cinco hashes bcrypt antes de abrir la transacción."""
    semaforo = asyncio.Semaphore(1)
    claves = {
        PASSWORD_ADMIN: "admin",
        PASSWORD_ADMIN2: "admin2",
        PASSWORD_VENDEDOR: "vendedor",
        PASSWORD_ANA: "ana",
        PASSWORD_NUEVO: "nuevo",
    }
    hashes: dict[str, str] = {}
    for password in claves:
        hashes[claves[password]] = await hashear_password(
            password, settings.BCRYPT_COST, semaforo
        )
    return hashes


async def cargar_datos(sesion: AsyncSession, hashes: dict[str, str]) -> bool:
    """Vacía las tablas y carga el estado inicial. Devuelve True si cargó."""
    await sesion.exec(text(f"TRUNCATE TABLE {TABLAS} RESTART IDENTITY CASCADE"))

    admin = Usuario(
        email="admin@example.com",
        nombre="Administrador Uno",
        password_hash=hashes["admin"],
    )
    admin2 = Usuario(
        email="admin2@example.com",
        nombre="Administrador Dos",
        password_hash=hashes["admin2"],
    )
    vendedor = Usuario(
        email="vendedor@example.com",
        nombre="Vendedor Uno",
        password_hash=hashes["vendedor"],
    )
    ana_usuario = Usuario(
        email="ana@example.com",
        nombre="Ana Paz",
        password_hash=hashes["ana"],
    )
    nuevo = Usuario(
        email="nuevo@example.com",
        nombre="Vendedor Nuevo",
        password_hash=hashes["nuevo"],
        debe_cambiar_password=True,
    )
    sesion.add_all([admin, admin2, vendedor, ana_usuario, nuevo])
    await sesion.flush()

    sesion.add_all(
        [
            AsignacionRol(usuario_id=admin.id, rol="ADMIN", otorgada_por=admin.id),
            AsignacionRol(usuario_id=admin2.id, rol="ADMIN", otorgada_por=admin.id),
            AsignacionRol(
                usuario_id=vendedor.id, rol="VENDEDOR", otorgada_por=admin.id
            ),
            AsignacionRol(usuario_id=ana_usuario.id, rol="CLIENTE"),
            AsignacionRol(usuario_id=nuevo.id, rol="VENDEDOR", otorgada_por=admin.id),
        ]
    )

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

    rayuela = Libro(
        isbn="978-950-00-0001-1",
        titulo="Rayuela",
        precio=Decimal("25000.00"),
        stock=0,
        editorial_id=sudamericana.id,
        genero_id=novela.id,
    )
    antologia = Libro(
        isbn="978-950-00-0002-8",
        titulo="Antología de la literatura fantástica",
        precio=Decimal("22000.00"),
        stock=0,
        editorial_id=emece.id,
        genero_id=cuento.id,
    )
    ficciones = Libro(
        isbn="978-950-00-0003-5",
        titulo="Ficciones",
        precio=Decimal("22000.00"),
        stock=0,
        editorial_id=sudamericana.id,
        genero_id=cuento.id,
    )
    respiracion = Libro(
        isbn="978-950-00-0004-2",
        titulo="Respiración artificial",
        precio=Decimal("27000.00"),
        stock=0,
        editorial_id=anagrama.id,
        genero_id=novela.id,
    )
    bestiario = Libro(
        isbn="978-950-00-0005-9",
        titulo="Bestiario",
        precio=Decimal("18000.00"),
        stock=0,
        editorial_id=sudamericana.id,
        genero_id=cuento.id,
    )
    sesion.add_all([rayuela, antologia, ficciones, respiracion, bestiario])
    await sesion.flush()

    sesion.add_all(
        [
            LibroAutor(libro_id=rayuela.id, autor_id=cortazar.id, rol="autor", orden=1),
            LibroAutor(
                libro_id=antologia.id, autor_id=borges.id, rol="coautor", orden=1
            ),
            LibroAutor(
                libro_id=antologia.id, autor_id=ocampo.id, rol="coautor", orden=2
            ),
            LibroAutor(
                libro_id=antologia.id, autor_id=bioy.id, rol="coautor", orden=3
            ),
            LibroAutor(
                libro_id=ficciones.id, autor_id=borges.id, rol="autor", orden=1
            ),
            LibroAutor(
                libro_id=respiracion.id, autor_id=piglia.id, rol="autor", orden=1
            ),
            LibroAutor(
                libro_id=bestiario.id, autor_id=cortazar.id, rol="autor", orden=1
            ),
        ]
    )

    lucia = Cliente(nombre="Lucía Fernández", email="lucia@example.com")
    tomas = Cliente(nombre="Tomás Ríos", email="tomas@example.com")
    ana = Cliente(
        nombre="Ana Paz", email="ana@example.com", usuario_id=ana_usuario.id
    )
    sesion.add_all([lucia, tomas, ana])
    await sesion.flush()

    sesion.add(
        PerfilCliente(
            cliente_id=lucia.id,
            telefono="11-5555-0101",
            direccion="Av. Corrientes 1234",
        )
    )

    venta = Venta(cliente_id=lucia.id, total=Decimal("69000.00"))
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
                libro_id=ficciones.id,
                cantidad=2,
                precio_unitario=ficciones.precio,
            ),
        ]
    )
    await sesion.flush()

    uow = UnitOfWork(sesion)
    for libro, cantidad in (
        (rayuela, 11),
        (antologia, 5),
        (ficciones, 10),
        (respiracion, 3),
        (bestiario, 1),
    ):
        await registrar_movimiento(
            uow,
            libro=libro,
            cantidad=cantidad,
            motivo="Stock inicial",
            usuario_id=admin.id,
        )

    await registrar_movimiento(
        uow,
        libro=rayuela,
        cantidad=-1,
        motivo="Venta",
        usuario_id=vendedor.id,
        venta_id=venta.id,
    )
    await registrar_movimiento(
        uow,
        libro=ficciones,
        cantidad=-2,
        motivo="Venta",
        usuario_id=vendedor.id,
        venta_id=venta.id,
    )

    sesion.add(
        EventoSeguridad(actor="SISTEMA", accion="Carga de los datos iniciales")
    )

    await sesion.commit()

    libros = (
        await sesion.exec(select(Libro).order_by(Libro.id))
    ).all()
    sumas = (
        await sesion.exec(
            select(MovimientoStock.libro_id, func.sum(MovimientoStock.cantidad))
            .group_by(MovimientoStock.libro_id)
            .order_by(MovimientoStock.libro_id)
        )
    ).all()
    totales = {libro_id: int(suma) for libro_id, suma in sumas}

    print("Seed completado.")
    print("  Usuarios: admin@example.com, admin2@example.com, vendedor@example.com,")
    print("            ana@example.com (CLIENTE) y nuevo@example.com (cambio pendiente).")
    print("  Libros (stock = suma de movimientos):")
    for libro in libros:
        print(
            f"    {libro.id}: {libro.titulo} -> stock {libro.stock} "
            f"(movimientos {totales.get(libro.id, 0)})"
        )
    print("  Venta 1: Lucía Fernández, 1 Rayuela + 2 Ficciones = 69000.00")
    print("  Evento de seguridad: SISTEMA - Carga de los datos iniciales")

    invariante = all(libro.stock == totales.get(libro.id, 0) for libro in libros)
    print(f"  Invariante stock == suma(movimientos): {'OK' if invariante else 'FALLA'}")
    return invariante


async def main() -> bool:
    settings = Settings()
    hashes = await _hashes(settings)
    engine = create_async_engine(settings.database_url, echo=False)
    try:
        fabrica = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with fabrica() as sesion:
            return await cargar_datos(sesion, hashes)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(main()) else 1)
