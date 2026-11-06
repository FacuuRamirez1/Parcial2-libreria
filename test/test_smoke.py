"""Prueba de humo: la app responde y la base de prueba está operativa."""

from httpx import AsyncClient


async def test_health_live_responde_200(cliente_http: AsyncClient) -> None:
    respuesta = await cliente_http.get("/health/live")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "vivo"}
