"""Validación del contrato de alta de venta (Ejercicio 5: RN-05)."""

from typing import Any

from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.ventas.models import RenglonVenta, Venta


async def test_venta_sin_renglones_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/", json={"cliente_id": cliente["id"], "renglones": []}
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Venta))).all() == []
    assert (await sesion.exec(select(RenglonVenta))).all() == []


async def test_libro_repetido_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [
                {"libro_id": libro["id"], "cantidad": 1},
                {"libro_id": libro["id"], "cantidad": 2},
            ],
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Venta))).all() == []
    assert (await sesion.exec(select(RenglonVenta))).all() == []


async def test_cantidad_cero_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [{"libro_id": libro["id"], "cantidad": 0}],
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Venta))).all() == []


async def test_precio_unitario_en_la_entrada_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [
                {"libro_id": libro["id"], "cantidad": 1, "precio_unitario": "10.00"}
            ],
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Venta))).all() == []


async def test_total_en_la_entrada_responde_422(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "total": "10.00",
            "renglones": [{"libro_id": libro["id"], "cantidad": 1}],
        },
    )

    assert respuesta.status_code == 422
    assert (await sesion.exec(select(Venta))).all() == []
