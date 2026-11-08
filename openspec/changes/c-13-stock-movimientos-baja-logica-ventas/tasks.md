# Tasks

> **Governance: ALTO.** El apply se hace con TDD estricto sobre pytest. No commitear sin orden explícita del usuario. Sin migración nueva.

## 0. Línea de base y arnés

- [x] 0.1 Verificar la base en `0004` (`alembic current`) y que `psql -U postgres` conecte (trust). Anotar el resultado. Verificación: `alembic current` = `0004`.
- [x] 0.2 Crear `tests/conftest.py`: base `libreria_test` (drop/create con asyncpg), `alembic upgrade head` por subprocess con env de prueba, `TRUNCATE ... RESTART IDENTITY CASCADE` por test, app con `lifespan_context`, `httpx.AsyncClient(ASGITransport)`, fixtures de usuarios ADMIN/VENDEDOR/CLIENTE con login real y de catálogo base. Verificación: `python -m pytest --collect-only` lista los tests sin errores.

## 1. Punto único de escritura de stock

- [x] 1.1 RED: test que crea un libro con `stock_inicial=4` y verifica `stock=4` + un movimiento `+4` "Stock inicial"; y `stock_inicial=0` sin movimiento. Verificación: falla (no existe `stock_inicial`/movimiento).
- [x] 1.2 GREEN: `app/modules/libros/stock.py` con `registrar_movimiento`; `LibroCreate.stock_inicial`; `crear_libro` crea con `stock=0` y aplica el movimiento. Verificación: test verde.
- [x] 1.3 TRIANGULATE: test de `PATCH /libros/{id}` con `stock` → 422 y con `precio` → 200 sin tocar stock. Verificación: verde.

## 2. Reposición e historial

- [x] 2.1 RED: tests de `POST /libros/{id}/reponer` (200, stock y movimiento), cantidad 0/negativa (422), libro dado de baja (409), inexistente (404); `GET /libros/{id}/movimientos` (200 ordenado, 404). Verificación: rojo.
- [x] 2.2 GREEN: `ReposicionIn`, `MovimientoStockRead`, `MovimientoStockRepository`, métodos del servicio y rutas ADMIN. Verificación: verde.

## 3. Baja lógica y re-alta

- [x] 3.1 RED: tests de `DELETE /libros/{id}` → 204 y sale del catálogo; repetida/inexistente → 404; re-alta del mismo ISBN → 201; segundo vigente → 409. Verificación: rojo.
- [x] 3.2 GREEN: `LibroRepository(SoftDeleteRepository)`, filtros `borrado_en IS NULL` en listado/conteo/detalle, `DELETE` con `soft_delete`. Verificación: verde.

## 4. Venta con stock

- [x] 4.1 RED: tests de venta exitosa (stock baja, movimiento `-1` ligado a la venta), dos renglones (dos movimientos), stock insuficiente (409 sin escrituras), libro dado de baja (409), cliente inexistente (409), invariante `stock = Σ movimientos`. Verificación: rojo.
- [x] 4.2 GREEN: `crear_venta(uow, datos, usuario_id)` con validación previa y `registrar_movimiento` por renglón; router pasa el usuario actual y agenda `BackgroundTasks` tras el commit. Verificación: verde.

## 5. Ventas propias y detalle con dueño

- [x] 5.1 RED: tests de `GET /mis-ventas` (solo propias, usuario sin ficha → página vacía, sin cookie → 401); `GET /ventas/{id}` (dueño 200, ajeno 403, personal 200, inexistente 404); detalle de venta con libro dado de baja muestra el título. Verificación: rojo.
- [x] 5.2 GREEN: ruta `GET /mis-ventas` y decisión de dueño en `obtener_venta` con roles vigentes de la misma sesión; quitar `requiere_rol` del detalle. Verificación: verde.

## 6. Cierre

- [x] 6.1 REFACTOR: revisar que `libro.stock` solo se asigne en `stock.py`, que no haya `commit()` en repositorios, que no haya carga perezosa y que `GET /ventas/{id}` mantenga 2 `SELECT`. Verificación: búsquedas y test de conteo de consultas.
- [x] 6.2 Correr la suite completa `python -m pytest -q`. Verificación: todo verde.
- [x] 6.3 Actualizar `CHANGES.md` (C-13 `[x]`) y el estado de las tasks. Verificación: diff revisado.
- [x] 6.4 `git status` y `git diff --stat` finales; no commitear sin orden. Verificación: salida anotada.
