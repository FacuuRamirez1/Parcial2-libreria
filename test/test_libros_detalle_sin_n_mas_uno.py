"""Lecturas de libro y venta sin N+1 (Ejercicio 6 / US-009)."""

from contextlib import contextmanager
from decimal import Decimal
from typing import Any, Callable, Iterator

from httpx import AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.libros.models import Libro


@contextmanager
def contar_selects(engine: AsyncEngine) -> Iterator[list[str]]:
    """Cuenta sentencias SELECT emitidas durante el bloque."""
    sentencias: list[str] = []

    def before_cursor_execute(
        conn, cursor, statement, parameters, context, executemany
    ) -> None:
        if statement.lstrip().upper().startswith("SELECT"):
            sentencias.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
    try:
        yield sentencias
    finally:
        event.remove(
            engine.sync_engine, "before_cursor_execute", before_cursor_execute
        )


async def _crear_autor(cliente_http: AsyncClient, nombre: str) -> dict[str, Any]:
    respuesta = await cliente_http.post(
        "/autores/", json={"nombre": nombre, "nacionalidad": "Argentina"}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def _crear_venta(
    cliente_http: AsyncClient, cliente_id: int, renglones: list[dict[str, int]]
) -> dict[str, Any]:
    respuesta = await cliente_http.post(
        "/ventas/", json={"cliente_id": cliente_id, "renglones": renglones}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def test_detalle_libro_precarga_editorial_genero_autores_con_dos_selects(
    engine: AsyncEngine,
    cliente_http: AsyncClient,
    crear_libro: Callable[..., Any],
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
) -> None:
    segundo = await _crear_autor(cliente_http, "Autora Dos")
    libro = await crear_libro(
        autores=[
            {"autor_id": autor["id"], "rol": "autor", "orden": 1},
            {"autor_id": segundo["id"], "rol": "coautor", "orden": 2},
        ]
    )

    with contar_selects(engine) as sentencias:
        respuesta = await cliente_http.get(f"/libros/{libro['id']}")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["editorial"]["id"] == editorial["id"]
    assert cuerpo["genero"]["id"] == genero["id"]
    assert [a["autor"]["nombre"] for a in cuerpo["autores"]] == [
        autor["nombre"],
        segundo["nombre"],
    ]
    assert cuerpo["autores"][1]["rol"] == "coautor"
    assert [a["orden"] for a in cuerpo["autores"]] == [1, 2]
    assert len(sentencias) == 2, sentencias


async def test_detalle_libro_con_tres_autores_mantiene_dos_selects(
    engine: AsyncEngine,
    cliente_http: AsyncClient,
    crear_libro: Callable[..., Any],
) -> None:
    autores = [await _crear_autor(cliente_http, f"Autor {i}") for i in range(3)]
    libro = await crear_libro(
        autores=[
            {"autor_id": a["id"], "rol": "autor", "orden": i + 1}
            for i, a in enumerate(autores)
        ]
    )

    with contar_selects(engine) as sentencias:
        respuesta = await cliente_http.get(f"/libros/{libro['id']}")

    assert respuesta.status_code == 200, respuesta.text
    assert len(respuesta.json()["autores"]) == 3
    assert len(sentencias) == 2, sentencias


async def test_detalle_libro_sin_genero_y_sin_autores(
    engine: AsyncEngine,
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    sesion: Any,
) -> None:
    libro = Libro(
        isbn="978-84-376-3000-1",
        titulo="Sin Genero",
        precio=Decimal("10.00"),
        stock=3,
        editorial_id=editorial["id"],
        genero_id=None,
    )
    sesion.add(libro)
    await sesion.commit()

    with contar_selects(engine) as sentencias:
        respuesta = await cliente_http.get(f"/libros/{libro.id}")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["genero"] is None
    assert cuerpo["autores"] == []
    assert len(sentencias) == 2, sentencias


async def test_listado_libros_precarga_detalle_con_tres_selects(
    engine: AsyncEngine,
    cliente_http: AsyncClient,
    crear_libro: Callable[..., Any],
    autor: dict[str, Any],
) -> None:
    await crear_libro(isbn="978-84-376-1000-1", autores=[
        {"autor_id": autor["id"], "rol": "autor", "orden": 1}
    ])
    await crear_libro(isbn="978-84-376-1000-2", titulo="Otro Libro")

    with contar_selects(engine) as sentencias:
        respuesta = await cliente_http.get("/libros/?page=1&size=20")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 2
    assert all("editorial" in item and "genero" in item for item in cuerpo["items"])
    assert [a["autor"]["nombre"] for a in cuerpo["items"][0]["autores"]] == [
        autor["nombre"]
    ]
    assert len(sentencias) == 3, sentencias


async def test_listado_vacio_ejecuta_solo_el_conteo(
    engine: AsyncEngine, cliente_http: AsyncClient
) -> None:
    with contar_selects(engine) as sentencias:
        respuesta = await cliente_http.get("/libros/?page=1&size=20")

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 0
    assert cuerpo["items"] == []
    assert len(sentencias) == 1, sentencias


async def test_detalle_venta_con_uno_y_tres_renglones_mantiene_dos_selects(
    engine: AsyncEngine,
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Callable[..., Any],
) -> None:
    libros = [
        await crear_libro(isbn=f"978-84-376-2000-{i}", titulo=f"Libro Venta {i}")
        for i in range(3)
    ]
    venta_uno = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libros[0]["id"], "cantidad": 1}]
    )
    venta_tres = await _crear_venta(
        cliente_http,
        cliente["id"],
        [
            {"libro_id": libros[0]["id"], "cantidad": 2},
            {"libro_id": libros[1]["id"], "cantidad": 1},
            {"libro_id": libros[2]["id"], "cantidad": 3},
        ],
    )

    with contar_selects(engine) as sentencias_uno:
        respuesta_uno = await cliente_http.get(f"/ventas/{venta_uno['id']}")
    with contar_selects(engine) as sentencias_tres:
        respuesta_tres = await cliente_http.get(f"/ventas/{venta_tres['id']}")

    assert respuesta_uno.status_code == 200, respuesta_uno.text
    assert respuesta_tres.status_code == 200, respuesta_tres.text
    assert len(sentencias_uno) == 2, sentencias_uno
    assert len(sentencias_tres) == 2, sentencias_tres
    renglones = respuesta_tres.json()["renglones"]
    assert len(renglones) == 3
    assert all("titulo" in r and "subtotal" in r for r in renglones)


async def test_detalle_venta_inexistente_404(
    cliente_http: AsyncClient,
) -> None:
    respuesta = await cliente_http.get("/ventas/999999")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Venta no encontrada"
