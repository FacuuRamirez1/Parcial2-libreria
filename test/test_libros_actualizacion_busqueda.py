"""Actualización completa de libros y búsqueda del catálogo (C-04 / caso C-08)."""

from typing import Any, Callable

from httpx import AsyncClient


async def test_patch_libro_actualiza_campos_del_contrato(
    cliente_http: AsyncClient,
    crear_libro: Callable[..., Any],
    editorial: dict[str, Any],
    genero: dict[str, Any],
) -> None:
    libro = await crear_libro()
    otra_editorial = await cliente_http.post(
        "/editoriales/", json={"nombre": "Otra Editorial", "pais": "Chile"}
    )
    otro_genero = await cliente_http.post("/generos/", json={"nombre": "Ensayo"})
    assert otra_editorial.status_code == 201, otra_editorial.text
    assert otro_genero.status_code == 201, otro_genero.text

    respuesta = await cliente_http.patch(
        f"/libros/{libro['id']}",
        json={
            "isbn": "978-84-376-9999-9",
            "titulo": "Titulo Actualizado",
            "precio": "30.50",
            "editorial_id": otra_editorial.json()["id"],
            "genero_id": otro_genero.json()["id"],
        },
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["isbn"] == "978-84-376-9999-9"
    assert cuerpo["titulo"] == "Titulo Actualizado"
    assert cuerpo["precio"] == "30.50"
    assert cuerpo["editorial_id"] == otra_editorial.json()["id"]
    assert cuerpo["genero_id"] == otro_genero.json()["id"]
    assert cuerpo["stock"] == libro["stock"]


async def test_patch_libro_sigue_rechazando_stock(
    cliente_http: AsyncClient, libro: dict[str, Any]
) -> None:
    respuesta = await cliente_http.patch(
        f"/libros/{libro['id']}", json={"stock": 99}
    )

    assert respuesta.status_code == 422, respuesta.text


async def test_busqueda_por_titulo_es_case_insensitive(
    cliente_http: AsyncClient, crear_libro: Callable[..., Any]
) -> None:
    await crear_libro(titulo="Cien Anos de Soledad", isbn="978-84-376-0000-1")
    await crear_libro(titulo="Rayuela", isbn="978-84-376-0000-5")

    respuesta = await cliente_http.get(
        "/libros/", params={"titulo": "cien anos"}
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert [item["titulo"] for item in cuerpo["items"]] == ["Cien Anos de Soledad"]


async def test_busqueda_por_titulo_no_permite_inyeccion(
    cliente_http: AsyncClient, crear_libro: Callable[..., Any]
) -> None:
    await crear_libro(titulo="Libro Seguro", isbn="978-84-376-0000-2")

    respuesta = await cliente_http.get(
        "/libros/", params={"titulo": "' OR 1=1 --"}
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["total"] == 0
    assert respuesta.json()["items"] == []


async def test_filtro_por_genero_devuelve_solo_coincidencias(
    cliente_http: AsyncClient,
    crear_libro: Callable[..., Any],
    genero: dict[str, Any],
) -> None:
    otro_genero = await cliente_http.post("/generos/", json={"nombre": "Poesia"})
    assert otro_genero.status_code == 201, otro_genero.text
    await crear_libro(titulo="Libro de Poesia", isbn="978-84-376-0000-3")
    await crear_libro(
        titulo="Libro de Poesia 2",
        isbn="978-84-376-0000-4",
        genero_id=otro_genero.json()["id"],
    )

    respuesta = await cliente_http.get(
        "/libros/", params={"genero_id": otro_genero.json()["id"]}
    )

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["genero_id"] == otro_genero.json()["id"]
