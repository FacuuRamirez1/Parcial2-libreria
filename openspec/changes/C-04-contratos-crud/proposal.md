# Proposal

## Why

C-03 deja el esquema de base de datos definido (tablas, restricciones, relaciones) pero no hay DTOs, endpoints ni repositorios de lectura/escritura sobre esas tablas. El Ejercicio 4 de la consigna (15 pts; US-005) exige contratos de entrada/salida separados de los modelos de tabla, endpoints CRUD paginados por recurso, traducción global de `IntegrityError` a HTTP 409 con mensaje propio, y el borrado lógico de libros (`DELETE /libros/{id}` → 204, soft delete con `borrado_en`). Sin este change, C-05 no puede construir altas con relaciones sobre contratos que no existen.

## What Changes

- **Nuevo archivo `app/core/paginacion.py`**: modelo genérico `PaginatedResponse[T]` (`items`, `total`, `page`, `size`, `pages`), validación de `page` (≥ 1) y `size` (1–100), cálculo de `pages` con `total == 0` → `pages = 1` y `items = []`, y `HTTPException 422` cuando `total > 0` y `page > pages`.
- **DTOs `Create/Update/Read` separados** en `app/modules/<modulo>/schemas.py` para editoriales, géneros, autores, libros y clientes; todos los DTOs de entrada con `ConfigDict(extra="forbid")`; salida de usuario sin `password_hash`.
- **DTOs de libros**: `LibroCreate` con `stock_inicial`, `LibroUpdate` sin campo `stock`, `ReponerStockRequest`, `LibroRead`.
- **DTOs de ventas**: `VentaCreate` sin precios ni totales (el servidor los calcula), `VentaRead`.
- **Endpoints por recurso**: `POST` (201 al crear), `GET` lista paginada, `GET {id}` (404 si inexistente), `PATCH {id}` con `exclude_unset` (excepto ventas, que no tiene PATCH); `DELETE /libros/{id}` → 204 con soft delete.
- **Repositorios específicos**: `LibroRepository` hereda de `SoftDeleteRepository` (usa `borrado_en`); `VentaRepository` precarga relaciones (cliente, renglones, libros) para evitar N+1.
- **Handler global de errores**: captura `IntegrityError` y lo traduce a HTTP 409 con mensaje propio (sin texto interno de la base, RN-12).
- **Archivos `test/*.http`** con respuesta esperada comentada para cada endpoint (ver `design.md` D-12).
- `main.py` registra los routers de los 6 módulos de dominio (además de `health`).

Fuera de alcance: lógica de transacción y altas con relaciones (C-05); consultas con `joinedload`/`selectinload` detalladas (C-05..C-06); aviso de comprobante con `BackgroundTasks` (C-07); autenticación, tests automatizados (`pytest`), `create_all` (prohibido).

## Capabilities

### New Capabilities

- `paginacion`: respuesta paginada estándar genérica y validación de `page`/`size`.
- `contratos-editoriales`, `contratos-generos`, `contratos-autores`, `contratos-libros`, `contratos-clientes`: DTOs de entrada/salida por módulo con `extra="forbid"` y campos exactos de la consigna.
- `contratos-ventas`: `VentaCreate` sin precios/totales, `VentaRead` con cálculo de servidor.
- `endpoints-crud`: `POST`/`GET` lista/`GET {id}`/`PATCH {id}` por recurso, `DELETE /libros/{id}` soft delete, 201 al crear, 404/409/422 con mensajes propios.
- `repositorios-modulo`: `LibroRepository` (soft delete) y `VentaRepository` (precarga de relaciones).
- `handler-integridad-global`: traducción de `IntegrityError` a 409 sin filtrar texto de la base.

### Modified Capabilities

- `app/main.py`: agrega `include_router` de los 6 routers de dominio (antes solo `health`).

## Impact

- **Código nuevo**: `app/core/paginacion.py`; `app/modules/{editoriales,generos,autores,libros,clientes}/schemas.py`, `service.py`, `router.py` (de docstring a implementación real); `app/modules/ventas/schemas.py`, `router.py` (solo `VentaCreate`/`VentaRead` y router, service en C-05).
- **Código modificado**: `app/main.py` (registro de routers).
- **API**: endpoints bajo `/editoriales`, `/generos`, `/autores`, `/libros`, `/clientes`, `/ventas` (GET lista paginada, GET {id}, POST, PATCH excepto ventas; DELETE /libros/{id}).
- **Base de datos**: ninguna (el esquema ya existe vía Alembic en C-03).
- **Dependencias**: ninguna nueva (usa `pydantic` de FastAPI, `fastapi.HTTPException`, `sqlalchemy.exc.IntegrityError`).
- **Changes posteriores**: C-05 depende de estos DTOs y endpoints para construir altas con transacciones (`UnitOfWork`); C-06/C-07 dependen de los nombres de relaciones precargadas en `VentaRepository`.

## Open Questions

- Ninguna que bloquee. C-03 es requisito previo (schema de base).
