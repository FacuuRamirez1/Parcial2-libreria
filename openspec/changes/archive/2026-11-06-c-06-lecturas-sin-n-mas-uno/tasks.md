# Tasks

> **TDD estricto**: cada comportamiento se escribe primero como test que falla (RED), luego el mínimo código (GREEN) y después se triangula con 0/1/N autores y 1/3 renglones.
>
> Reglas duras: sin carga perezosa (`lazy="raise"`), colecciones con `selectinload` y relaciones a uno con `joinedload` en la misma consulta; sin `create_all`; handlers `async def`; no commitear sin orden del usuario.

## 1. Detalle de libro

- [x] 1.1 RED: crear `test/test_libros_detalle_sin_n_mas_uno.py` con el listener `before_cursor_execute` y un test que exija `GET /libros/{id}` con `editorial`, `genero` y `autores`, y exactamente 2 `SELECT`.
- [x] 1.2 GREEN de contrato: agregar `LibroAutorRead` y `LibroDetalleRead` en `app/modules/libros/schemas.py` reutilizando `EditorialRead`, `GeneroRead` y `AutorRead`.
- [x] 1.3 GREEN de repositorio: agregar `_opciones_detalle()` y `get_by_id_con_detalle(id)` a `LibroRepository` (`joinedload` editorial/género, `selectinload` autorías→autor).
- [x] 1.4 GREEN de service/router: mapear el detalle con un helper explícito y cambiar `GET /libros/{id}` a `response_model=LibroDetalleRead`.
- [x] 1.5 TRIANGULATE: cubrir libro sin género, sin autores y con 3 autores; verificar que el conteo sigue siendo 2.

## 2. Listado de libros con detalle

- [x] 2.1 RED: test que exija `GET /libros/` con `editorial`/`genero`/`autores` por ítem y exactamente 3 `SELECT` con 1 vs. varios libros.
- [x] 2.2 GREEN: aplicar `_opciones_detalle()` en `get_all_filtrado` y cambiar el listado a `PaginatedResponse[LibroDetalleRead]`.
- [x] 2.3 TRIANGULATE: listado vacío (`total = 0`, 1 `SELECT` de conteo) y listado con autores; verificar que no hay consultas por fila.

## 3. Detalle de venta

- [x] 3.1 RED: test que mida `GET /ventas/{id}` con 1 vs. 3 renglones y exija 2 `SELECT` y los campos `titulo`/`subtotal`.
- [x] 3.2 GREEN: si el conteo no es fijo, corregir las opciones de precarga en `VentaRepository`/service; si ya es fijo, dejar el código intacto y documentar la evidencia.
- [x] 3.3 TRIANGULATE: venta con un renglón y venta inexistente (404).

## 4. Chequeo integral

- [x] 4.1 Ejecutar la suite completa con `TEST_DATABASE_URL` y registrar el conteo de tests. Evidencia 2026-11-06: 64 tests en verde, incluidos 7 de `test_libros_detalle_sin_n_mas_uno.py`.
- [x] 4.2 Auditar que ninguna lectura de libro/venta acceda a relaciones sin precarga (`grep` de `lazy="raise"` y revisión de services).
- [x] 4.3 `openspec validate c-06-lecturas-sin-n-mas-uno --strict` sin errores y archivar el change.

## Workflow follow-up

- C-07 reutiliza las precargas de venta para agendar el aviso con `BackgroundTasks`.
- `CHANGES.md` se marca `[x]` al archivar (fuera de este change).
