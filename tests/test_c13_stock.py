"""C-13 — alta con stock inicial, reposición, historial y PATCH sin stock."""

import pytest

from tests import ayuda


async def test_alta_con_stock_inicial_deja_movimiento(cliente, usuarios, sesiones, catalogo, fabrica):
    respuesta = await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)
    assert respuesta.status_code == 201, respuesta.text
    libro = respuesta.json()
    assert libro["stock"] == 4

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT cantidad, motivo, usuario_id, venta_id FROM movimiento_stock "
        "WHERE libro_id = :libro ORDER BY id",
        libro=libro["id"],
    )
    assert movimientos == [
        {
            "cantidad": 4,
            "motivo": "Stock inicial",
            "usuario_id": usuarios["admin"]["usuario_id"],
            "venta_id": None,
        }
    ]


async def test_alta_con_stock_inicial_cero_no_deja_movimiento(cliente, sesiones, catalogo, fabrica):
    respuesta = await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=0)
    assert respuesta.status_code == 201, respuesta.text
    libro = respuesta.json()
    assert libro["stock"] == 0

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT id FROM movimiento_stock WHERE libro_id = :libro",
        libro=libro["id"],
    )
    assert movimientos == []


async def test_patch_con_stock_responde_422_y_no_cambia_el_stock(cliente, sesiones, catalogo):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.patch(f"/libros/{libro['id']}", json={"stock": 99})
    assert respuesta.status_code == 422, respuesta.text
    assert "stock" in respuesta.text

    detalle = await cliente.get(f"/libros/{libro['id']}")
    assert detalle.json()["stock"] == 4


async def test_patch_de_precio_no_toca_el_stock(cliente, sesiones, catalogo):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.patch(f"/libros/{libro['id']}", json={"precio": "1600.00"})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["precio"] == "1600.00"
    assert respuesta.json()["stock"] == 4


async def test_reponer_suma_stock_y_deja_movimiento(cliente, usuarios, sesiones, catalogo, fabrica):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["stock"] == 5

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT cantidad, motivo, usuario_id FROM movimiento_stock "
        "WHERE libro_id = :libro ORDER BY id",
        libro=libro["id"],
    )
    assert movimientos[-1] == {
        "cantidad": 3,
        "motivo": "Reposición",
        "usuario_id": usuarios["admin"]["usuario_id"],
    }


@pytest.mark.parametrize("cantidad", [0, -1])
async def test_reponer_con_cantidad_no_positiva_es_422(cliente, sesiones, catalogo, cantidad):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": cantidad})
    assert respuesta.status_code == 422, respuesta.text

    detalle = await cliente.get(f"/libros/{libro['id']}")
    assert detalle.json()["stock"] == 2


async def test_reponer_un_libro_inexistente_es_404(cliente, sesiones):
    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.post("/libros/999999/reponer", json={"cantidad": 1})
    assert respuesta.status_code == 404


async def test_movimientos_ordenados_tras_alta_reposicion_y_venta(
    cliente, usuarios, sesiones, catalogo
):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (
        await cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 3})
    ).status_code == 200

    venta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 2}],
    )
    assert venta.status_code == 201, venta.text

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.get(f"/libros/{libro['id']}/movimientos")
    assert respuesta.status_code == 200, respuesta.text
    movimientos = respuesta.json()

    assert [m["cantidad"] for m in movimientos] == [4, 3, -2]
    assert [m["motivo"] for m in movimientos] == ["Stock inicial", "Reposición", "Venta"]
    assert all(m["libro_id"] == libro["id"] for m in movimientos)
    assert movimientos[-1]["venta_id"] == venta.json()["id"]


async def test_movimientos_de_un_libro_inexistente_es_404(cliente, sesiones):
    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.get("/libros/999999/movimientos")
    assert respuesta.status_code == 404


async def test_movimientos_incluyen_un_libro_dado_de_baja(cliente, sesiones, catalogo):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    respuesta = await cliente.get(f"/libros/{libro['id']}/movimientos")
    assert respuesta.status_code == 200, respuesta.text
    assert [m["cantidad"] for m in respuesta.json()] == [4]

async def test_alta_con_stock_inicial_negativo_es_422(cliente, sesiones, catalogo):
    respuesta = await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=-1)
    assert respuesta.status_code == 422, respuesta.text


async def test_alta_con_stock_y_stock_inicial_es_422(cliente, sesiones, catalogo):
    respuesta = await ayuda.crear_libro(
        cliente, sesiones["admin"], catalogo, stock=4, stock_inicial=4
    )
    assert respuesta.status_code == 422, respuesta.text


async def test_reponer_con_campo_extra_es_422(cliente, sesiones, catalogo):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.post(
        f"/libros/{libro['id']}/reponer", json={"cantidad": 1, "motivo": "manual"}
    )
    assert respuesta.status_code == 422, respuesta.text
    assert (await cliente.get(f"/libros/{libro['id']}")).json()["stock"] == 2


async def test_movimientos_de_libro_dado_de_baja_conservan_la_venta(
    cliente, usuarios, sesiones, catalogo
):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()
    venta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert venta.status_code == 201, venta.text

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    respuesta = await cliente.get(f"/libros/{libro['id']}/movimientos")
    assert respuesta.status_code == 200, respuesta.text
    movimientos = respuesta.json()
    assert [m["cantidad"] for m in movimientos] == [4, -1]
    assert movimientos[-1]["venta_id"] == venta.json()["id"]


async def test_re_alta_no_mezcla_los_movimientos_de_cada_libro(
    cliente, sesiones, catalogo, fabrica
):
    viejo = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01", stock_inicial=4)
    ).json()
    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{viejo['id']}")).status_code == 204

    nuevo = (
        await ayuda.crear_libro(
            cliente,
            sesiones["admin"],
            catalogo,
            isbn="978-950-01",
            titulo="Rayuela (nueva edición)",
            stock_inicial=2,
        )
    ).json()

    filas = await ayuda.fetch(
        fabrica,
        "SELECT libro_id, cantidad FROM movimiento_stock ORDER BY id",
    )
    assert filas == [
        {"libro_id": viejo["id"], "cantidad": 4},
        {"libro_id": nuevo["id"], "cantidad": 2},
    ]
