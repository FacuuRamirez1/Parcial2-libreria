"""Alta del perfil único de un cliente (Ejercicio 5: US-007)."""

from typing import Any

from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.clientes.models import PerfilCliente

MENSAJE_DUPLICADO = "El cliente ya tiene un perfil asociado"
MENSAJE_INEXISTENTE = "Cliente no encontrado"


async def test_alta_correcta_responde_201(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={"telefono": "555-0100", "direccion": "Calle Falsa 123"},
    )

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["cliente_id"] == cliente["id"]
    assert cuerpo["telefono"] == "555-0100"
    assert cuerpo["direccion"] == "Calle Falsa 123"
    assert len((await sesion.exec(select(PerfilCliente))).all()) == 1


async def test_segundo_perfil_responde_409(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
) -> None:
    primero = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={"telefono": "555-0100", "direccion": "Calle Falsa 123"},
    )
    assert primero.status_code == 201, primero.text

    segundo = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={"telefono": "555-0101", "direccion": "Otra dirección"},
    )

    assert segundo.status_code == 409
    assert segundo.json()["detail"] == MENSAJE_DUPLICADO


async def test_cliente_inexistente_responde_409_con_mensaje_propio(
    cliente_http: AsyncClient,
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/clientes/999999/perfil",
        json={"telefono": "555-0100", "direccion": "Calle Falsa 123"},
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == MENSAJE_INEXISTENTE
    assert respuesta.json()["detail"] != MENSAJE_DUPLICADO
    assert (await sesion.exec(select(PerfilCliente))).all() == []


async def test_cliente_id_inconsistente_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={
            "telefono": "555-0100",
            "direccion": "Calle Falsa 123",
            "cliente_id": cliente["id"] + 1,
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(PerfilCliente))).all() == []


async def test_telefono_de_31_caracteres_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={"telefono": "1" * 31, "direccion": "Calle Falsa 123"},
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(PerfilCliente))).all() == []


async def test_campo_extra_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        f"/clientes/{cliente['id']}/perfil",
        json={
            "telefono": "555-0100",
            "direccion": "Calle Falsa 123",
            "campo_desconocido": True,
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(PerfilCliente))).all() == []
