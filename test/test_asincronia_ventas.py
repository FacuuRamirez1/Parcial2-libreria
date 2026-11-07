"""Pruebas del aviso de comprobante en segundo plano y de la asincronía (C-07)."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.modules.ventas import service as ventas_service

RAIZ = Path(__file__).resolve().parent.parent
LOGGER_VENTAS = "app.modules.ventas.service"


async def _venta(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    renglones: list[dict[str, int]],
) -> dict[str, Any]:
    respuesta = await cliente_http.post(
        "/ventas/",
        json={"cliente_id": cliente["id"], "renglones": renglones},
    )
    assert respuesta.status_code == 201, respuesta.text
    return respuesta.json()


async def test_post_venta_ejecuta_el_aviso_y_lo_registra(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Callable[..., Any],
    caplog: Any,
) -> None:
    libro = await crear_libro()
    caplog.set_level(logging.INFO, logger=LOGGER_VENTAS)

    inicio = time.perf_counter()
    respuesta = await cliente_http.post(
        "/ventas/",
        json={
            "cliente_id": cliente["id"],
            "renglones": [{"libro_id": libro["id"], "cantidad": 1}],
        },
    )
    transcurrido = time.perf_counter() - inicio

    assert respuesta.status_code == 201, respuesta.text
    venta = respuesta.json()
    assert transcurrido >= 0.45, "el aviso debe esperar 0.5 s antes de registrar"

    mensajes = [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == LOGGER_VENTAS
    ]
    assert any(
        "Aviso" in mensaje
        and str(venta["id"]) in mensaje
        and str(venta["total"]) in mensaje
        for mensaje in mensajes
    ), mensajes


async def test_aviso_usa_el_total_de_una_venta_con_dos_renglones(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Callable[..., Any],
    caplog: Any,
) -> None:
    libro_a = await crear_libro(
        isbn="978-84-376-0494-7", titulo="Libro A", precio="25.00"
    )
    libro_b = await crear_libro(
        isbn="978-84-376-0495-4", titulo="Libro B", precio="10.50"
    )
    caplog.set_level(logging.INFO, logger=LOGGER_VENTAS)

    venta = await _venta(
        cliente_http,
        cliente,
        [
            {"libro_id": libro_a["id"], "cantidad": 2},
            {"libro_id": libro_b["id"], "cantidad": 1},
        ],
    )

    assert venta["total"] == "60.50"
    mensajes = [
        registro.getMessage()
        for registro in caplog.records
        if registro.name == LOGGER_VENTAS
    ]
    assert any(
        "Aviso" in mensaje
        and str(venta["id"]) in mensaje
        and "60.50" in mensaje
        for mensaje in mensajes
    ), mensajes


async def test_el_aviso_no_bloquea_otra_peticion(
    cliente_http: AsyncClient,
    cliente: dict[str, Any],
    crear_libro: Callable[..., Any],
    monkeypatch: Any,
) -> None:
    libro = await crear_libro()
    inicio_aviso = asyncio.Event()
    liberar_aviso = asyncio.Event()
    llamadas = 0

    async def pausa_controlada() -> None:
        nonlocal llamadas
        llamadas += 1
        inicio_aviso.set()
        await liberar_aviso.wait()

    monkeypatch.setattr(ventas_service, "_esperar_aviso", pausa_controlada)

    tarea_venta = asyncio.create_task(
        cliente_http.post(
            "/ventas/",
            json={
                "cliente_id": cliente["id"],
                "renglones": [{"libro_id": libro["id"], "cantidad": 1}],
            },
        )
    )
    await asyncio.wait_for(inicio_aviso.wait(), timeout=2)
    assert llamadas == 1
    assert not tarea_venta.done(), "el aviso debe correr después de la respuesta"

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as otro_cliente:
        inicio_health = time.perf_counter()
        health = await otro_cliente.get("/health/live")
        transcurrido_health = time.perf_counter() - inicio_health

    assert health.status_code == 200
    assert transcurrido_health < 0.3, "el event loop no debe estar bloqueado"
    assert not tarea_venta.done()

    liberar_aviso.set()
    respuesta = await asyncio.wait_for(tarea_venta, timeout=2)
    assert respuesta.status_code == 201, respuesta.text


def test_app_no_usa_llamadas_bloqueantes() -> None:
    patrones = ("time.sleep", "import requests", "requests.")
    infracciones: list[str] = []
    for archivo in (RAIZ / "app").rglob("*.py"):
        texto = archivo.read_text(encoding="utf-8")
        for patron in patrones:
            if patron in texto:
                infracciones.append(f"{archivo.relative_to(RAIZ)}: {patron}")

    assert infracciones == [], "Llamadas bloqueantes en app/: " + ", ".join(infracciones)
