"""C-13 — baja lógica, salida del catálogo y re-alta del ISBN."""

from tests import ayuda


async def test_baja_logica_saca_el_libro_del_catalogo(cliente, sesiones, catalogo, fabrica):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.delete(f"/libros/{libro['id']}")
    assert respuesta.status_code == 204, respuesta.text
    assert respuesta.content == b""

    fila = await ayuda.fetch(
        fabrica, "SELECT borrado_en FROM libro WHERE id = :id", id=libro["id"]
    )
    assert fila[0]["borrado_en"] is not None

    listado = await cliente.get("/libros/")
    assert listado.status_code == 200
    assert libro["id"] not in [item["id"] for item in listado.json()["items"]]
    assert listado.json()["total"] == 0

    detalle = await cliente.get(f"/libros/{libro['id']}")
    assert detalle.status_code == 404


async def test_baja_repetida_y_baja_inexistente_son_404(cliente, sesiones, catalogo):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 404
    assert (await cliente.delete("/libros/999999")).status_code == 404


async def test_re_alta_del_mismo_isbn_es_201(cliente, sesiones, catalogo, fabrica):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01")).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    respuesta = await ayuda.crear_libro(
        cliente,
        sesiones["admin"],
        catalogo,
        isbn="978-950-01",
        titulo="Rayuela (nueva edición)",
    )
    assert respuesta.status_code == 201, respuesta.text
    assert respuesta.json()["id"] != libro["id"]

    filas = await ayuda.fetch(
        fabrica,
        "SELECT id, borrado_en FROM libro WHERE isbn = :isbn ORDER BY id",
        isbn="978-950-01",
    )
    assert len(filas) == 2
    assert filas[0]["borrado_en"] is not None
    assert filas[1]["borrado_en"] is None


async def test_un_segundo_libro_vigente_con_el_mismo_isbn_es_409(cliente, sesiones, catalogo):
    primero = await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01")
    assert primero.status_code == 201, primero.text

    segundo = await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01")
    assert segundo.status_code == 409, segundo.text
    assert "detail" in segundo.json()


async def test_reponer_un_libro_dado_de_baja_es_409_sin_movimiento(
    cliente, sesiones, catalogo, fabrica
):
    libro = (await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    respuesta = await cliente.post(f"/libros/{libro['id']}/reponer", json={"cantidad": 2})
    assert respuesta.status_code == 409, respuesta.text

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT cantidad FROM movimiento_stock WHERE libro_id = :libro",
        libro=libro["id"],
    )
    assert [m["cantidad"] for m in movimientos] == [4]
