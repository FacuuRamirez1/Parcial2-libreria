"""C-13 — venta con descuento de stock, atomicidad e invariante."""

from tests import ayuda


async def test_venta_descuenta_stock_y_deja_movimiento(
    cliente, usuarios, sesiones, catalogo, fabrica
):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)
    ).json()

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 2}],
    )
    assert respuesta.status_code == 201, respuesta.text
    venta = respuesta.json()
    assert venta["total"] == "3000.00"

    detalle = (await cliente.get(f"/libros/{libro['id']}")).json()
    assert detalle["stock"] == 2

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT cantidad, motivo, venta_id, usuario_id FROM movimiento_stock "
        "WHERE libro_id = :libro ORDER BY id",
        libro=libro["id"],
    )
    assert movimientos[0]["cantidad"] == 4
    assert movimientos[1] == {
        "cantidad": -2,
        "motivo": "Venta",
        "venta_id": venta["id"],
        "usuario_id": usuarios["vendedor"]["usuario_id"],
    }


async def test_venta_con_dos_renglones_deja_dos_movimientos(
    cliente, usuarios, sesiones, catalogo, fabrica
):
    rayuela = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01", stock_inicial=4)
    ).json()
    ficciones = (
        await ayuda.crear_libro(
            cliente,
            sesiones["admin"],
            catalogo,
            isbn="978-950-02",
            titulo="Ficciones",
            precio="2000.00",
            stock_inicial=3,
        )
    ).json()

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [
            {"libro_id": rayuela["id"], "cantidad": 1},
            {"libro_id": ficciones["id"], "cantidad": 2},
        ],
    )
    assert respuesta.status_code == 201, respuesta.text
    venta = respuesta.json()
    assert len(venta["renglones"]) == 2
    assert venta["total"] == "5500.00"

    movimientos = await ayuda.fetch(
        fabrica,
        "SELECT libro_id, cantidad FROM movimiento_stock WHERE venta_id = :venta ORDER BY id",
        venta=venta["id"],
    )
    assert movimientos == [
        {"libro_id": rayuela["id"], "cantidad": -1},
        {"libro_id": ficciones["id"], "cantidad": -2},
    ]


async def test_stock_insuficiente_es_atomico(cliente, usuarios, sesiones, catalogo, fabrica):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=1)
    ).json()

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 2}],
    )
    assert respuesta.status_code == 409, respuesta.text

    ventas = await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta")
    assert ventas[0]["n"] == 0
    movimientos = await ayuda.fetch(fabrica, "SELECT cantidad FROM movimiento_stock")
    assert [m["cantidad"] for m in movimientos] == [1]
    assert (await cliente.get(f"/libros/{libro['id']}")).json()["stock"] == 1


async def test_libro_inexistente_es_409_sin_escrituras(cliente, usuarios, sesiones, fabrica):
    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": 999999, "cantidad": 1}],
    )
    assert respuesta.status_code == 409, respuesta.text
    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta"))[0]["n"] == 0
    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM movimiento_stock"))[0]["n"] == 0


async def test_cliente_inexistente_es_409_sin_escrituras(cliente, sesiones, catalogo, fabrica):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        999999,
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert respuesta.status_code == 409, respuesta.text
    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta"))[0]["n"] == 0
    assert (await cliente.get(f"/libros/{libro['id']}")).json()["stock"] == 2


async def test_vender_un_libro_dado_de_baja_es_409(cliente, usuarios, sesiones, catalogo, fabrica):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert respuesta.status_code == 409, respuesta.text
    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta"))[0]["n"] == 0
    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM movimiento_stock"))[0]["n"] == 1


async def test_invariante_stock_es_suma_de_movimientos(
    cliente, usuarios, sesiones, catalogo, fabrica
):
    rayuela = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01", stock_inicial=4)
    ).json()
    ficciones = (
        await ayuda.crear_libro(
            cliente,
            sesiones["admin"],
            catalogo,
            isbn="978-950-02",
            titulo="Ficciones",
            precio="2000.00",
            stock_inicial=1,
        )
    ).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (
        await cliente.post(f"/libros/{rayuela['id']}/reponer", json={"cantidad": 3})
    ).status_code == 200

    assert (
        await ayuda.vender(
            cliente,
            sesiones["vendedor"],
            usuarios["ana"]["cliente_id"],
            [{"libro_id": rayuela["id"], "cantidad": 2}],
        )
    ).status_code == 201
    assert (
        await ayuda.vender(
            cliente,
            sesiones["vendedor"],
            usuarios["otro"]["cliente_id"],
            [{"libro_id": ficciones["id"], "cantidad": 1}],
        )
    ).status_code == 201

    libros = await ayuda.fetch(fabrica, "SELECT id, stock FROM libro ORDER BY id")
    movimientos = await ayuda.fetch(
        fabrica, "SELECT libro_id, cantidad FROM movimiento_stock ORDER BY id"
    )
    ayuda.assert_invariante_stock(movimientos, libros)

async def test_stock_insuficiente_en_el_segundo_renglon_no_deja_escrituras(
    cliente, usuarios, sesiones, catalogo, fabrica
):
    rayuela = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01", stock_inicial=4)
    ).json()
    ficciones = (
        await ayuda.crear_libro(
            cliente,
            sesiones["admin"],
            catalogo,
            isbn="978-950-02",
            titulo="Ficciones",
            precio="2000.00",
            stock_inicial=1,
        )
    ).json()

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [
            {"libro_id": rayuela["id"], "cantidad": 1},
            {"libro_id": ficciones["id"], "cantidad": 2},
        ],
    )
    assert respuesta.status_code == 409, respuesta.text

    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta"))[0]["n"] == 0
    movimientos = await ayuda.fetch(
        fabrica, "SELECT libro_id, cantidad FROM movimiento_stock ORDER BY id"
    )
    assert movimientos == [
        {"libro_id": rayuela["id"], "cantidad": 4},
        {"libro_id": ficciones["id"], "cantidad": 1},
    ]
    assert (await cliente.get(f"/libros/{rayuela['id']}")).json()["stock"] == 4
    assert (await cliente.get(f"/libros/{ficciones['id']}")).json()["stock"] == 1


async def test_libro_dado_de_baja_entre_varios_renglones_es_409_sin_escrituras(
    cliente, usuarios, sesiones, catalogo, fabrica
):
    rayuela = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, isbn="978-950-01", stock_inicial=4)
    ).json()
    ficciones = (
        await ayuda.crear_libro(
            cliente,
            sesiones["admin"],
            catalogo,
            isbn="978-950-02",
            titulo="Ficciones",
            precio="2000.00",
            stock_inicial=2,
        )
    ).json()

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{ficciones['id']}")).status_code == 204

    respuesta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [
            {"libro_id": rayuela["id"], "cantidad": 1},
            {"libro_id": ficciones["id"], "cantidad": 1},
        ],
    )
    assert respuesta.status_code == 409, respuesta.text

    assert (await ayuda.fetch(fabrica, "SELECT count(*) AS n FROM venta"))[0]["n"] == 0
    assert (await cliente.get(f"/libros/{rayuela['id']}")).json()["stock"] == 4
    movimientos = await ayuda.fetch(
        fabrica, "SELECT libro_id, cantidad FROM movimiento_stock ORDER BY id"
    )
    assert movimientos == [
        {"libro_id": rayuela["id"], "cantidad": 4},
        {"libro_id": ficciones["id"], "cantidad": 2},
    ]
