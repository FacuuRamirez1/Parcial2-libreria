"""Contrato de paginación `page`/`size` en los listados CRUD (regresión C-04).

Los routers de editoriales, géneros y autores deben consumir la tupla que
devuelve `get_paginacion` igual que libros, clientes y ventas. Antes del fix
indexaban la tupla como diccionario (`pag["offset"]`), lo que producía un 500.
"""

import pytest
from httpx import AsyncClient

RECURSOS = [
    ("/editoriales/", {"nombre": "Editorial Paginada", "pais": "Argentina"}),
    ("/generos/", {"nombre": "Genero Paginado"}),
    ("/autores/", {"nombre": "Autor Paginado", "nacionalidad": "Argentina"}),
]


@pytest.mark.parametrize(("ruta", "payload"), RECURSOS)
async def test_listado_responde_200_con_page_y_size(
    cliente_http: AsyncClient, ruta: str, payload: dict[str, object]
) -> None:
    creada = await cliente_http.post(ruta, json=payload)
    assert creada.status_code == 201, creada.text

    respuesta = await cliente_http.get(ruta, params={"page": 1, "size": 1})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["page"] == 1
    assert cuerpo["size"] == 1
    assert cuerpo["total"] == 1
    assert cuerpo["pages"] == 1
    assert len(cuerpo["items"]) == 1


@pytest.mark.parametrize(("ruta", "payload"), RECURSOS)
async def test_listado_calcula_offset_a_partir_de_page(
    cliente_http: AsyncClient, ruta: str, payload: dict[str, object]
) -> None:
    primero = await cliente_http.post(ruta, json=payload)
    assert primero.status_code == 201, primero.text
    segundo = await cliente_http.post(
        ruta, json={**payload, "nombre": f"{payload['nombre']} 2"}
    )
    assert segundo.status_code == 201, segundo.text

    respuesta = await cliente_http.get(ruta, params={"page": 2, "size": 1})

    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["page"] == 2
    assert cuerpo["total"] == 2
    assert cuerpo["pages"] == 2
    assert [item["id"] for item in cuerpo["items"]] == [segundo.json()["id"]]
