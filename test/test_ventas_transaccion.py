"""Persistencia transaccional del alta de venta (Ejercicio 5)."""

from typing import Any

from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.modules.ventas.models import RenglonVenta, Venta


async def test_la_venta_persiste_tras_el_201(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    alta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [{"libro_id": libro["id"], "cantidad": 2}],
        },
    )
    assert alta.status_code == 201, alta.text

    consulta = await cliente_http.get(f"/ventas/{alta.json()['id']}")

    assert consulta.status_code == 200, consulta.text
    assert consulta.json()["id"] == alta.json()["id"]
    assert consulta.json()["cliente_id"] == cliente["id"]


async def test_los_renglones_quedan_asociados_a_la_venta(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
    crear_libro: Any,
    sesion: AsyncSession,
) -> None:
    segundo = await crear_libro(isbn="978-84-376-0495-1", titulo="Segundo Libro")
    alta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [
                {"libro_id": libro["id"], "cantidad": 1},
                {"libro_id": segundo["id"], "cantidad": 2},
            ],
        },
    )
    assert alta.status_code == 201, alta.text

    venta_id = alta.json()["id"]
    consulta = await sesion.exec(select(RenglonVenta).where(RenglonVenta.venta_id == venta_id))
    renglones = consulta.all()
    assert len(renglones) == 2
    assert all(r.venta_id == venta_id for r in renglones)


async def test_cliente_inexistente_no_deja_filas(
    cliente_http: AsyncClient,
    libro: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": 999999,
            "renglones": [{"libro_id": libro["id"], "cantidad": 1}],
        },
    )

    assert respuesta.status_code == 409
    assert (await sesion.exec(select(Venta))).all() == []
    assert (await sesion.exec(select(RenglonVenta))).all() == []


async def test_libro_inexistente_no_deja_filas(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    sesion: AsyncSession,
) -> None:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [{"libro_id": 999999, "cantidad": 1}],
        },
    )

    assert respuesta.status_code == 409
    assert (await sesion.exec(select(Venta))).all() == []
    assert (await sesion.exec(select(RenglonVenta))).all() == []
