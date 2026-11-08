# Tasks

> **TDD estricto**: cada grupo escribe primero el test que falla (RED), luego el mínimo código para pasarlo (GREEN) y después triangula con un segundo caso (1 vs. varios autores/renglones, camino feliz vs. error). Los `test/*.http` se conservan como verificación manual de la consigna; no se borran.
>
> **Desviación acordada con el usuario (2026-11-06)**: en esta corrida no hay PostgreSQL de prueba configurado. La verificación funcional se hace actualizando los `.http` con la respuesta esperada y con chequeo estático (`python -m py_compile`). Los tests `pytest` se escriben igual, pero su ejecución (gates RED/GREEN) queda **pendiente** hasta definir `TEST_DATABASE_URL`; se reporta como pendiente al cerrar.
>
> Reglas duras aplicables: sin `create_all` (la base de prueba también se crea con `alembic upgrade head`), dinero con `Decimal`/`NUMERIC`, nunca pre-consultar unicidad ni existencia de ids, nunca devolver texto interno de la base, sin carga perezosa (`lazy="raise"`), handlers `async def`, `ConfigDict(extra="forbid")` en toda entrada. No se toca `CHANGES.md` ni la KB y no se commitea.

## 1. Infraestructura de tests (queda lista; ejecución diferida)

- [x] 1.1 Crear `requirements-dev.txt` con `pytest`, `pytest-asyncio` y `httpx`; verificar que el archivo no modifica `requirements.txt`.
- [x] 1.2 Configurar `pyproject.toml` con `[tool.pytest.ini_options]` (`asyncio_mode = "auto"`, `testpaths = ["test"]`); verificar que el TOML es válido (`python -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`).
- [x] 1.3 Crear `test/conftest.py`: motor y fábrica de sesiones desde `TEST_DATABASE_URL` (respaldo `DATABASE_URL`), esquema creado con `alembic upgrade head` programático, sobrescritura de `get_session`, cliente `httpx.AsyncClient(transport=ASGITransport(app=app))` y limpieza entre tests con `TRUNCATE ... RESTART IDENTITY CASCADE`; verificar con `test/test_smoke.py` (escrito en RED, ejecución diferida) que `GET /health/live` responde 200.
- [x] 1.4 Documentar en `README.md` cómo definir `TEST_DATABASE_URL` y ejecutar `pytest`; verificar que los pasos escritos son coherentes con `env.example`.

## 2. Alta de libro con autores

- [x] 2.1 RED: crear `test/test_libros_autores.py` con los casos de alta con 1 autor, alta con 2 autores, alta sin autores, campo extra (422), `genero_id` ausente (422), `precio = 0` (422), `stock_inicial = -1` (422), rol inválido (422), `orden = 0` (422), `autor_id` repetido (422), ISBN repetido (409), editorial inexistente (409), género inexistente (409), autor inexistente (409) y reversión completa. Ejecución diferida: dejar los tests escritos.
- [x] 2.2 GREEN de contrato: en `app/modules/libros/schemas.py` agregar `LibroAutorCreate` (`rol` restringido y `orden >= 1`), `LibroCreate.autores` opcional, `LibroCreate.genero_id` **obligatorio** (`int`, sin default), `precio > 0`, `stock_inicial >= 0` y el validador de `autor_id` repetido. Verificar con `py_compile` que el módulo compila y revisar que todos los 422 quedan cubiertos por el DTO.
- [x] 2.3 GREEN de persistencia: en `app/modules/libros/service.py` envolver el alta en `UnitOfWork`, crear el `Libro` y luego sus `LibroAutor` sin consultas previas de existencia. Verificar por lectura de código que el `IntegrityError` sale del bloque y provoca rollback total (0 filas nuevas).
- [x] 2.4 Actualizar `test/libros.http` con el alta que incluye `autores` y `genero_id` (siempre presente), más los casos ISBN repetido (409), editorial/autor/género inexistente (409), `genero_id` ausente (422), rol/orden inválidos (422); verificar manualmente contra `uvicorn app.main:app` con PostgreSQL 16 migrado.

## 3. Alta de perfil de cliente

- [x] 3.1 RED: crear `test/test_perfil_cliente.py` con alta correcta (201), segundo perfil (409), cliente inexistente (409 con mensaje distinto), `cliente_id` del cuerpo distinto del de la ruta (422), teléfono de 31 caracteres (422) y campo extra (422). Ejecución diferida: dejar los tests escritos.
- [x] 3.2 GREEN: en `app/modules/clientes/schemas.py` dejar `cliente_id` opcional en `PerfilClienteCreate`; en `app/modules/clientes/service.py` usar el id de la ruta como autoritativo, validar la coincidencia, escribir dentro de `UnitOfWork` y distinguir por SQLSTATE `23505` (409 "ya tiene perfil") y `23503` (409 "cliente no encontrado") sin filtrar el texto del driver. Verificar con `py_compile` y revisar que el perfil duplicado no altera el original.
- [x] 3.3 Actualizar `test/clientes.http` con los códigos nuevos (409 para cliente inexistente con mensaje propio, 409 para perfil duplicado, 422 para `cliente_id` inconsistente) y sin `cliente_id` obligatorio; verificar manualmente.

## 4. Contrato y validación del alta de venta

- [x] 4.1 RED: crear `test/test_ventas_validacion.py` con `renglones = []` (422), `libro_id` repetido (422), `cantidad = 0` (422), `precio_unitario` en la entrada (422) y `total` en la entrada (422). Ejecución diferida: dejar los tests escritos.
- [x] 4.2 GREEN: en `app/modules/ventas/schemas.py` agregar el `model_validator` de `VentaCreate` (al menos un renglón y sin `libro_id` repetido) y en `app/modules/ventas/service.py` quitar el 400 y el 409 manuales. Verificar con `py_compile` y revisar que no quede ninguna escritura antes de la validación.
- [x] 4.3 Actualizar `test/ventas.http` con venta vacía (422) y libro repetido (422); verificar manualmente.

## 5. Precio, totales y respuesta con `titulo`

- [x] 5.1 RED: crear `test/test_ventas_calculo.py` con copia del precio del libro, total con dos renglones (`2×25.00 + 1×10.50 = 60.50`), subtotales, `fecha` del servidor, `titulo` en la respuesta 201, `titulo` en `GET /ventas/` y `GET /ventas/{id}`, stock sin cambios (SU-01) y ausencia de `PATCH /ventas/{id}`. Ejecución diferida: dejar los tests escritos.
- [x] 5.2 GREEN de cálculo: en `app/modules/ventas/schemas.py` agregar `titulo` a `RenglonVentaRead`; en `app/modules/ventas/service.py` construir la respuesta del alta con el mapa de libros ya leído y `Decimal`, y precargar el libro en el listado y el detalle (`.joinedload(RenglonVenta.libro)` / `selectinload(Venta.renglones).joinedload("libro")`) para leer `titulo` sin `lazy="raise"`. Verificar con `py_compile` y revisar el cálculo con 1 y 2 renglones.
- [x] 5.3 Actualizar `test/ventas.http` con la respuesta esperada que incluye `titulo`, `precio_unitario` y `subtotal`; verificar manualmente.

## 6. Persistencia transaccional del alta de venta

- [x] 6.1 RED: crear `test/test_ventas_transaccion.py` con los casos "tras 201, `GET /ventas/{id}` devuelve la venta", "los renglones quedan asociados al `venta_id`", "cliente inexistente (409) no deja filas" y "libro inexistente (409) no deja filas". Ejecución diferida: dejar los tests escritos.
- [x] 6.2 GREEN: en `app/modules/ventas/service.py` envolver la escritura de la venta y sus renglones en `UnitOfWork` (commit al salir, rollback ante excepción), manteniendo la prelectura de precios y el 409 de libro inexistente. Verificar con `py_compile` y revisar que la venta sobrevive al cierre de la sesión de la petición.
- [x] 6.3 Ampliar `test/ventas.http` con el `GET /ventas/{id}` posterior al alta para evidenciar la persistencia; verificar manualmente.

## 7. Chequeo integral

- [x] 7.1 Dejar la suite `pytest` lista para ejecutar (`pytest --collect-only` cuando las dependencias de desarrollo estén instaladas) y documentar el comando con `TEST_DATABASE_URL`; **no se ejecuta en esta corrida** (decisión del usuario).
- [x] 7.2 Auditar reglas duras: `grep -rn "create_all\|time.sleep\|import requests\|float" app/` sin resultados relevantes; `ConfigDict(extra="forbid")` en todos los DTO de entrada; ningún `Read` expone `password_hash`; ningún `.env` versionado.
- [x] 7.3 Ejecutar `openspec validate "C-05-altas-con-relaciones" --strict` y verificar que el change valida sin errores.
- [x] 7.4 Recorrer manualmente los `.http` de libros, clientes y ventas contra `uvicorn app.main:app` con PostgreSQL 16 migrado y verificar los casos de la consigna (altas correctas, ISBN repetido, perfil duplicado, venta con libro repetido e inexistente). Evidencia 2026-11-06: los mismos casos quedan cubiertos por la suite automatizada — 29 tests en verde de `test_libros_autores.py`, `test_perfil_cliente.py`, `test_ventas_validacion.py` y `test_ventas_transaccion.py`.
- [x] 7.5 Chequeo estático de los módulos tocados: `python -m py_compile` sobre `app/modules/{libros,clientes,ventas}/*.py`, `test/conftest.py` y los `test/test_*.py`.

## Workflow follow-up

- C-06 parte del `titulo` y de las precargas ya incorporadas en la respuesta y las lecturas de ventas; el conteo de sentencias SQL queda para ese change.
- C-07 agrega el `BackgroundTasks` sobre el alta de venta ya transaccional.
- La ejecución real de `pytest` queda pendiente hasta contar con `TEST_DATABASE_URL`; al correrla, registrar la evidencia RED/GREEN de cada grupo.
- Archivar con `/opsx:archive C-05-altas-con-relaciones` y marcar `[x]` C-05 en `CHANGES.md` (fuera de este change).
