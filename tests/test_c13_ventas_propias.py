"""C-13 — ventas propias y detalle de venta para el dueño o el personal."""

from tests import ayuda


async def test_mis_ventas_devuelve_solo_las_propias(cliente, usuarios, sesiones, catalogo):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=4)
    ).json()

    venta_ana = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert venta_ana.status_code == 201, venta_ana.text

    venta_otro = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["otro"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert venta_otro.status_code == 201, venta_otro.text

    ayuda.sesion(cliente, sesiones["ana"])
    respuesta = await cliente.get("/mis-ventas")
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    assert [item["id"] for item in cuerpo["items"]] == [venta_ana.json()["id"]]


async def test_mis_ventas_de_un_usuario_sin_ficha_de_cliente_es_vacia(
    cliente, sesiones, catalogo
):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()
    assert (
        await ayuda.vender(
            cliente, sesiones["vendedor"], 1, [{"libro_id": libro["id"], "cantidad": 1}]
        )
    ).status_code == 201

    ayuda.sesion(cliente, sesiones["admin"])
    respuesta = await cliente.get("/mis-ventas")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["items"] == []
    assert respuesta.json()["total"] == 0


async def test_mis_ventas_sin_sesion_es_401(cliente):
    cliente.cookies.clear()
    assert (await cliente.get("/mis-ventas")).status_code == 401


async def test_mis_ventas_con_pagina_fuera_de_rango_es_422(cliente, usuarios, sesiones, catalogo):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()
    assert (
        await ayuda.vender(
            cliente,
            sesiones["vendedor"],
            usuarios["ana"]["cliente_id"],
            [{"libro_id": libro["id"], "cantidad": 1}],
        )
    ).status_code == 201

    ayuda.sesion(cliente, sesiones["ana"])
    assert (await cliente.get("/mis-ventas?page=99&size=20")).status_code == 422


async def test_detalle_de_venta_para_dueno_personal_y_ajeno(
    cliente, usuarios, sesiones, catalogo
):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()
    venta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert venta.status_code == 201, venta.text
    venta_id = venta.json()["id"]

    ayuda.sesion(cliente, sesiones["ana"])
    assert (await cliente.get(f"/ventas/{venta_id}")).status_code == 200

    ayuda.sesion(cliente, sesiones["otro"])
    assert (await cliente.get(f"/ventas/{venta_id}")).status_code == 403

    ayuda.sesion(cliente, sesiones["vendedor"])
    assert (await cliente.get(f"/ventas/{venta_id}")).status_code == 200

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.get(f"/ventas/{venta_id}")).status_code == 200


async def test_detalle_de_venta_inexistente_es_404_y_sin_sesion_401(
    cliente, usuarios, sesiones, catalogo
):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()
    venta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    venta_id = venta.json()["id"]

    ayuda.sesion(cliente, sesiones["ana"])
    assert (await cliente.get("/ventas/999999")).status_code == 404

    cliente.cookies.clear()
    assert (await cliente.get(f"/ventas/{venta_id}")).status_code == 401


async def test_detalle_de_venta_muestra_el_titulo_de_un_libro_dado_de_baja(
    cliente, usuarios, sesiones, catalogo
):
    libro = (
        await ayuda.crear_libro(cliente, sesiones["admin"], catalogo, stock_inicial=2)
    ).json()
    venta = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1}],
    )
    assert venta.status_code == 201, venta.text

    ayuda.sesion(cliente, sesiones["admin"])
    assert (await cliente.delete(f"/libros/{libro['id']}")).status_code == 204

    ayuda.sesion(cliente, sesiones["ana"])
    respuesta = await cliente.get(f"/ventas/{venta.json()['id']}")
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["renglones"][0]["titulo"] == "Rayuela"

async def test_detalle_de_venta_usa_el_mismo_numero_de_consultas_con_dos_o_cuatro_renglones(
    cliente, usuarios, sesiones, catalogo
):
    libros = []
    for indice in range(1, 5):
        libro = (
            await ayuda.crear_libro(
                cliente,
                sesiones["admin"],
                catalogo,
                isbn=f"978-950-02-0{indice}",
                titulo=f"Libro consultas {indice}",
                precio=f"{1000 * indice}.00",
                stock_inicial=4,
            )
        ).json()
        libros.append(libro)

    venta_dos = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1} for libro in libros[:2]],
    )
    venta_cuatro = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": libro["id"], "cantidad": 1} for libro in libros],
    )
    assert venta_dos.status_code == 201, venta_dos.text
    assert venta_cuatro.status_code == 201, venta_cuatro.text

    ayuda.sesion(cliente, sesiones["admin"])
    async with ayuda.contar_consultas(cliente.app.state.engine) as con_dos:
        assert (await cliente.get(f"/ventas/{venta_dos.json()['id']}")).status_code == 200
    async with ayuda.contar_consultas(cliente.app.state.engine) as con_cuatro:
        assert (await cliente.get(f"/ventas/{venta_cuatro.json()['id']}")).status_code == 200

    assert len(con_dos) == len(con_cuatro), (
        f"2 renglones: {len(con_dos)} consultas; 4 renglones: {len(con_cuatro)}"
    )


async def test_detalle_de_venta_usa_el_mismo_numero_de_consultas_con_uno_o_dos_renglones(
    cliente, usuarios, sesiones, catalogo
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
            stock_inicial=4,
        )
    ).json()

    venta_uno = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [{"libro_id": rayuela["id"], "cantidad": 1}],
    )
    venta_dos = await ayuda.vender(
        cliente,
        sesiones["vendedor"],
        usuarios["ana"]["cliente_id"],
        [
            {"libro_id": rayuela["id"], "cantidad": 1},
            {"libro_id": ficciones["id"], "cantidad": 1},
        ],
    )
    assert venta_uno.status_code == 201, venta_uno.text
    assert venta_dos.status_code == 201, venta_dos.text

    ayuda.sesion(cliente, sesiones["admin"])
    async with ayuda.contar_consultas(cliente.app.state.engine) as con_uno:
        assert (await cliente.get(f"/ventas/{venta_uno.json()['id']}")).status_code == 200
    async with ayuda.contar_consultas(cliente.app.state.engine) as con_dos:
        assert (await cliente.get(f"/ventas/{venta_dos.json()['id']}")).status_code == 200

    assert len(con_uno) == len(con_dos)
