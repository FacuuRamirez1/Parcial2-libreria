# Proposal

> **Governance: ALTO** (stock, transacciones de venta, borrado lógico y permisos por dueño). El `/opsx:apply` implementa en pasos con tests pytest; no se commitea sin orden explícita del usuario.

## Why

C-10 dejó creadas las tablas `movimiento_stock` y la columna `libro.borrado_en`, y C-12 dejó la autorización por roles. Falta el comportamiento que las usa: el stock todavía se escribe por PATCH, vender no descuenta stock, no existe la baja lógica ni la re-alta de ISBN, y `GET /ventas/{id}` sigue restringido al personal sin decisión de dueño. El Ejercicio 6 (parte 2) y el Ejercicio 8 del Parcial exigen un único punto de escritura de stock, movimientos de alta/reposición/venta, baja lógica, venta atómica con descuento y detalle de venta como dueño o personal (RN-09..RN-14).

## What Changes

- **Punto único de escritura de stock**: una función `registrar_movimiento(...)` actualiza `libro.stock` y agrega la fila de `movimiento_stock` en el mismo paso. La usan el alta del libro, la reposición y la venta. Ningún otro lugar escribe `libro.stock`.
- **`POST /libros`** acepta `stock_inicial` (en lugar de `stock`) y deja el movimiento "Stock inicial" (si es > 0) en el mismo Unit of Work. **BREAKING** para el contrato del TP.
- **`PATCH /libros/{id}`** deja de aceptar `stock` (con `extra="forbid"` responde **422**). Sigue aceptando título, precio, ISBN, editorial y género.
- **`POST /libros/{id}/reponer`** (ADMIN): suma stock y agrega un movimiento positivo en un solo UoW; libro dado de baja → 409, inexistente → 404.
- **`GET /libros/{id}/movimientos`** (ADMIN): historial de movimientos del libro, 404 si no existe.
- **`DELETE /libros/{id}`** (ADMIN): baja lógica (`borrado_en`), **204**; el libro sale del catálogo. El mismo ISBN puede volver a cargarse (**201**); un segundo libro vigente con ese ISBN → **409**. Vender o reponer un libro dado de baja → **409**.
- **`POST /ventas`**: en un solo UoW lee los libros vigentes, copia precios, calcula el total, inserta venta y renglones, descuenta stock y agrega un movimiento negativo por renglón. Stock insuficiente, libro/cliente inexistente o libro dado de baja → **409** sin escrituras parciales. El aviso `BackgroundTasks` se agenda después del commit.
- **`GET /mis-ventas`** (solo autenticado): ventas del cliente asociado al usuario actual, con envoltorio de paginación.
- **`GET /ventas/{id}`**: deja de exigir rol; el servicio decide dueño o personal (403 si no corresponde, 404 si no existe). El detalle sigue mostrando el título de libros dados de baja con número fijo de consultas.
- **Pruebas**: suite `pytest` (no existía) contra una base PostgreSQL de prueba migrada con Alembic; cubre stock, movimientos, baja/re-alta, venta atómica, invariante `stock = Σ movimientos` y permisos.

## Capabilities

### New Capabilities

- `stock-movimientos`: punto único de escritura de stock, movimientos de alta/reposición/venta, historial y prohibición de editar stock por PATCH.
- `baja-logica-libros`: baja lógica de un libro, salida del catálogo, re-alta del mismo ISBN y rechazo de venta/reposición sobre libros dados de baja.
- `ventas-con-stock`: venta atómica con descuento de stock y un movimiento por renglón, rechazos sin escrituras parciales e invariante stock = suma de movimientos.
- `ventas-propias`: `GET /mis-ventas` y decisión de dueño o personal en `GET /ventas/{id}`.

### Modified Capabilities

- `altas-ventas`: la venta descuenta stock y deja movimientos (reemplaza SU-01 del TP); rechaza libros dados de baja y stock insuficiente con 409.
- `repositorios-libros`: `LibroRepository` pasa a `SoftDeleteRepository`, filtra los dados de baja y agrega el historial de movimientos.
- `repositorios-ventas`: el detalle de venta sigue con precarga fija aunque el libro esté dado de baja.
- `matriz-permisos`: declara `DELETE /libros/{id}`, `POST /libros/{id}/reponer` y `GET /libros/{id}/movimientos` (ADMIN); `GET /mis-ventas` (autenticado) y `GET /ventas/{id}` sin rol con decisión de dueño.
- `detalle-libros`: `GET /libros/{id}` y el catálogo excluyen libros dados de baja.

## Impact

- **Código nuevo**: `app/modules/libros/stock.py` (punto único de escritura), `MovimientoStockRepository`, contratos `ReposicionIn` y `MovimientoStockRead`, rutas de reposición, movimientos y baja; `GET /mis-ventas`.
- **Código modificado**: `app/modules/libros/{models? no, ya existe, schemas,repository,service,router,unit_of_work}.py`; `app/modules/ventas/{service,repository,router}.py`; `app/main.py` solo si cambia el montaje (las rutas viven en los routers existentes).
- **Esquema**: **sin migración** — `movimiento_stock`, `libro.borrado_en` y el índice único parcial del ISBN ya existen desde 0003/0004 (C-10).
- **Pruebas**: `tests/` con `conftest.py`, fixtures de base de prueba y casos de C-13; no hay runner previo.
- **Fuera de alcance**: seed definitivo y `.http` finales (C-14); carreras/concurrencia (cap. 7).
