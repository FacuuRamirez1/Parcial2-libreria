"""Precio copiado, totales y respuesta con título (Ejercicio 5: RN-06, RN-07)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from httpx import AsyncClient


def _decimal(valor: Any) -> Decimal:
    return Decimal(str(valor))


async def _crear_venta(
    cliente_http: AsyncClient, cliente_id: int, renglones: list[dict[str, int]]
) -> dict[str, Any]:
    respuesta = await cliente_http.post(
        "/ventas/", json={"cliente_id": cliente_id, "renglones": renglones}
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def test_copia_el_precio_del_libro(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Any,
) -> None:
    libro = await crear_libro(precio="25.00")

    cuerpo = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    renglon = cuerpo["renglones"][0]
    assert _decimal(renglon["precio_unitario"]) == Decimal("25.00")
    assert _decimal(renglon["subtotal"]) == Decimal("25.00")


async def test_total_y_subtotales_con_dos_renglones(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Any,
) -> None:
    libro_a = await crear_libro(precio="25.00", titulo="Libro A")
    libro_b = await crear_libro(
        isbn="978-84-376-0495-1", precio="10.50", titulo="Libro B"
    )

    cuerpo = await _crear_venta(
        cliente_http,
        cliente["id"],
        [
            {"libro_id": libro_a["id"], "cantidad": 2},
            {"libro_id": libro_b["id"], "cantidad": 1},
        ],
    )

    assert _decimal(cuerpo["total"]) == Decimal("60.50")
    por_libro = {r["libro_id"]: r for r in cuerpo["renglones"]}
    assert _decimal(por_libro[libro_a["id"]]["subtotal"]) == Decimal("50.00")
    assert _decimal(por_libro[libro_b["id"]]["subtotal"]) == Decimal("10.50")


async def test_fecha_la_pone_el_servidor(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    antes = datetime.now(UTC)

    cuerpo = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    fecha = datetime.fromisoformat(cuerpo["fecha"])
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=UTC)
    assert antes - timedelta(seconds=5) <= fecha <= datetime.now(UTC) + timedelta(seconds=5)


async def test_respuesta_201_incluye_titulo(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    cuerpo = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    renglon = cuerpo["renglones"][0]
    assert renglon["titulo"] == libro["titulo"]
    assert "precio_unitario" in renglon
    assert "subtotal" in renglon


async def test_get_ventas_incluye_titulo(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    respuesta = await cliente_http.get("/ventas/")

    assert respuesta.status_code == 200, respuesta.text
    renglon = respuesta.json()["items"][0]["renglones"][0]
    assert renglon["titulo"] == libro["titulo"]
    assert "precio_unitario" in renglon
    assert "subtotal" in renglon


async def test_get_venta_por_id_incluye_titulo(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    creada = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    respuesta = await cliente_http.get(f"/ventas/{creada['id']}")

    assert respuesta.status_code == 200, respuesta.text
    renglon = respuesta.json()["renglones"][0]
    assert renglon["titulo"] == libro["titulo"]
    assert "precio_unitario" in renglon
    assert "subtotal" in renglon


async def test_la_venta_no_modifica_el_stock(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 3}]
    )

    respuesta = await cliente_http.get(f"/libros/{libro['id']}")

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["stock"] == libro["stock"]


async def test_no_existe_patch_de_ventas(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    libro: dict[str, Any],
) -> None:
    creada = await _crear_venta(
        cliente_http, cliente["id"], [{"libro_id": libro["id"], "cantidad": 1}]
    )

    respuesta = await cliente_http.patch(f"/ventas/{creada['id']}", json={"total": "1.00"})

    assert respuesta.status_code == 405
