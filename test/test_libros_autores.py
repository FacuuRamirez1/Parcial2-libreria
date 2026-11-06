"""Alta de libro con autorías (Ejercicio 5: US-006)."""

from typing import Any

from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.libros.models import Libro, LibroAutor


def _payload(
    editorial_id: int, genero_id: int, **cambios: Any
) -> dict[str, Any]:
    datos: dict[str, Any] = {
        "isbn": "978-84-376-0494-7",
        "titulo": "Cien años de soledad",
        "precio": "25.00",
        "stock_inicial": 10,
        "editorial_id": editorial_id,
        "genero_id": genero_id,
    }
    datos.update(cambios)
    return datos


async def test_alta_con_un_autor_persiste_libro_autor(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[{"autor_id": autor["id"], "rol": "autor", "orden": 1}],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 201, respuesta.text
    libro_id = respuesta.json()["id"]
    filas = (await sesion.exec(select(LibroAutor).where(LibroAutor.libro_id == libro_id))).all()
    assert len(filas) == 1
    assert filas[0].autor_id == autor["id"]
    assert filas[0].rol == "autor"
    assert filas[0].orden == 1


async def test_alta_con_dos_autores(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    segundo = await cliente_http.post(
        "/autores/", json={"nombre": "Otro Autor", "nacionalidad": "Chile"}
    )
    assert segundo.status_code == 201, segundo.text
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[
            {"autor_id": autor["id"], "rol": "autor", "orden": 1},
            {"autor_id": segundo.json()["id"], "rol": "coautor", "orden": 2},
        ],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 201, respuesta.text
    libro_id = respuesta.json()["id"]
    filas = (await sesion.exec(select(LibroAutor).where(LibroAutor.libro_id == libro_id))).all()
    assert len(filas) == 2
    assert {f.rol for f in filas} == {"autor", "coautor"}


async def test_alta_sin_autores_crea_libro_sin_autorias(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(editorial["id"], genero["id"])

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 201, respuesta.text
    libro_id = respuesta.json()["id"]
    filas = (await sesion.exec(select(LibroAutor).where(LibroAutor.libro_id == libro_id))).all()
    assert filas == []


async def test_campo_extra_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(editorial["id"], genero["id"], campo_desconocido=True)

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_genero_id_ausente_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = {
        "isbn": "978-84-376-0494-7",
        "titulo": "Sin género",
        "precio": "25.00",
        "stock_inicial": 10,
        "editorial_id": editorial["id"],
    }

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_precio_cero_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(editorial["id"], genero["id"], precio="0")

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_stock_inicial_negativo_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(editorial["id"], genero["id"], stock_inicial=-1)

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_rol_invalido_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[{"autor_id": autor["id"], "rol": "editor", "orden": 1}],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_orden_cero_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[{"autor_id": autor["id"], "rol": "autor", "orden": 0}],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_autor_id_repetido_responde_422(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    autor: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[
            {"autor_id": autor["id"], "rol": "autor", "orden": 1},
            {"autor_id": autor["id"], "rol": "coautor", "orden": 2},
        ],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Libro))).all() == []


async def test_isbn_repetido_responde_409(
    cliente_http: AsyncClient,
    libro: dict[str, Any],
    editorial: dict[str, Any],
    genero: dict[str, Any],
) -> None:
    datos = _payload(editorial["id"], genero["id"], isbn=libro["isbn"])

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 409
    assert "detail" in respuesta.json()


async def test_editorial_inexistente_responde_409(
    cliente_http: AsyncClient,
    genero: dict[str, Any],
) -> None:
    datos = _payload(999999, genero["id"])

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 409
    assert "detail" in respuesta.json()


async def test_genero_inexistente_responde_409(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
) -> None:
    datos = _payload(editorial["id"], 999999)

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 409
    assert "detail" in respuesta.json()


async def test_autor_inexistente_responde_409_y_revierte_todo(
    cliente_http: AsyncClient,
    editorial: dict[str, Any],
    genero: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    datos = _payload(
        editorial["id"],
        genero["id"],
        autores=[{"autor_id": 999999, "rol": "autor", "orden": 1}],
    )

    respuesta = await cliente_http.post("/libros/", json=datos)

    assert respuesta.status_code == 409
    assert "detail" in respuesta.json()
    assert (await sesion.exec(select(Libro))).all() == []
    assert (await sesion.exec(select(LibroAutor))).all() == []
