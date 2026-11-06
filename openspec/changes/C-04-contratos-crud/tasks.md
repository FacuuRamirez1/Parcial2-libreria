# Tasks

> **Verificación**: archivos `.http` en `test/` con respuesta esperada comentada (como exige la consigna), ejecutados contra PostgreSQL 16 real con `alembic upgrade head` aplicado (C-03). Cada tarea indica cómo se verifica. Referencias: `design.md` (D-01..D-07) y `specs/`.
>
> Reglas duras: sin `create_all` (en ninguna base), `Decimal`/`NUMERIC` para dinero, nunca pre-consultar unicidad/existencia (UNIQUE/FK rechazan → 409), nunca texto interno de la base (traducir `IntegrityError` a mensaje propio), nunca carga perezosa (joinedload/selectinload en la misma consulta), todo handler `async def`, `ConfigDict(extra="forbid")` en todo DTO de entrada, salida de usuario sin `password_hash`, `DELETE /libros/{id}` → 204 soft delete, sin PATCH de ventas. No commitear sin orden del usuario.

## 1. Paginación estandarizada

- [ ] 1.1 Crear `app/core/paginacion.py` con `PaginatedResponse[T]` (items, total, page, size, pages), `calcular_paginas(total, size)` y dependencia `get_paginacion(page=1, size=20)` con `page ≥ 1`, `size` 1–100; `total == 0` → `pages = 1`, `items = []`; `total > 0` y `page > pages` → `HTTPException 422` (D-01).
  - Verificación (`.http`): `GET /editoriales/?page=0` → 422; `GET /editoriales/?size=101` → 422; `GET /editoriales/?page=999` sobre catálogo vacío → 200 con `pages=1`, `items=[]`, `total=0`; `GET /editoriales/?page=2` con 1 registro y `size=1` → 422.

## 2. Schemas / contratos por módulo

- [ ] 2.1 `app/modules/editoriales/schemas.py`: `EditorialCreate`, `EditorialUpdate`, `EditorialRead` con `ConfigDict(extra="forbid")` en los de entrada (D-02).
- [ ] 2.2 `app/modules/generos/schemas.py`: `GeneroCreate`, `GeneroUpdate`, `GeneroRead` con `ConfigDict(extra="forbid")` en entrada (D-02).
- [ ] 2.3 `app/modules/autores/schemas.py`: `AutorCreate`, `AutorUpdate`, `AutorRead` con `ConfigDict(extra="forbid")` en entrada (D-02).
- [ ] 2.4 `app/modules/libros/schemas.py`: `LibroCreate` con `stock_inicial`, `LibroUpdate` **sin** `stock`, `ReponerStockRequest` (`cantidad`), `LibroRead`; `ConfigDict(extra="forbid")` en los de entrada (D-02).
- [ ] 2.5 `app/modules/clientes/schemas.py`: `ClienteCreate`, `ClienteUpdate`, `ClienteRead`, `PerfilClienteCreate`, `PerfilClienteRead` con `ConfigDict(extra="forbid")` en entrada (D-02).
- [ ] 2.6 `app/modules/usuarios/schemas.py`: `UsuarioRead` sin `password_hash` (ocultar de toda salida) (D-02).
- [ ] 2.7 `app/modules/ventas/schemas.py`: `VentaCreate` **sin** precios ni totales, `VentaRead` con `total` y `renglones` (D-02).
  - Verificación (`.http`): `POST /editoriales/` con campo extra → 422 (`extra="forbid"`); `POST /libros/` con `stock` en `LibroUpdate` → 422; `GET /usuarios/{id}` nunca devuelve `password_hash`.

## 3. Endpoints CRUD por recurso

- [ ] 3.1 `app/modules/editoriales/router.py` + `service.py`: `POST` (201), `GET` lista paginada, `GET {id}` (200/404), `PATCH {id}` (200, `exclude_unset`) (D-03).
- [ ] 3.2 `app/modules/generos/router.py` + `service.py`: igual que editoriales (D-03).
- [ ] 3.3 `app/modules/autores/router.py` + `service.py`: igual que editoriales (D-03).
- [ ] 3.4 `app/modules/libros/router.py` + `service.py`: `POST` (201), `GET` lista paginada, `GET {id}` (200/404), `PATCH {id}` (200), `DELETE /libros/{id}` → 204 soft delete (D-03).
- [ ] 3.5 `app/modules/clientes/router.py` + `service.py`: `POST` (201), `GET` lista paginada, `GET {id}` (200/404), `PATCH {id}` (200) (D-03).
- [ ] 3.6 `app/modules/ventas/router.py`: `POST` (201, con `VentaCreate` sin precios/totales), `GET` lista paginada, `GET {id}` (200/404); **sin PATCH** (D-03).
- [ ] 3.7 `app/main.py`: registrar los 6 routers de dominio además de `health` (D-06).
  - Verificación (`.http`): cada módulo responde 201 al crear, 200 al listar (paginado), 200 al GET {id} existente, 404 al GET {id} inexistente, 200 al PATCH {id} (excepto ventas), 204 al DELETE /libros/{id}, 409 ante duplicado (UNIQUE), 422 al paginación fuera de rango.

## 4. Repositorios específicos por módulo

- [ ] 4.1 `app/modules/libros/repository.py`: `LibroRepository(SoftDeleteRepository[Libro])` — hereda filtros `borrado_en IS NULL` y `soft_delete` (D-04).
- [ ] 4.2 `app/modules/ventas/repository.py`: `VentaRepository(BaseRepository[Venta])` con `get_con_detalle(id)` que usa `joinedload` (cliente) y `selectinload` (renglones → libro) (D-04).
  - Verificación (código): `issubclass(LibroRepository, SoftDeleteRepository)` es `True`; `VentaRepository.get_con_detalle` declara `joinedload`/`selectinload` en la misma consulta.

## 5. Handler global de `IntegrityError`

- [ ] 5.1 Implementar `@app.exception_handler(IntegrityError)` (o en `app/core/errors.py`) que devuelva 409 con mensaje propio sin texto de la base; también `DataError` → 422 con mensaje propio (D-05).
  - Verificación (`.http`): `POST /editoriales/` con nombre repetido → 409 `{"detail": "..."}` sin nombre de restricción ni SQL; `POST /libros/` con `isbn` de 18 caracteres → 422 (`DataError` red de seguridad).

## 6. Archivos `.http` de prueba

- [ ] 6.1 Crear `test/editoriales.http`, `test/generos.http`, `test/autores.http`, `test/libros.http`, `test/clientes.http`, `test/ventas.http` con cada endpoint y su respuesta esperada comentada (D-07).
  - Verificación: ejecutar cada `.http` contra `uvicorn app.main:app` con PostgreSQL 16 y `alembic upgrade head` aplicado; todas las respuestas coinciden con el comentario esperado.

## 7. Chequeo integral y auditoría de reglas duras

- [ ] 7.1 `grep -rn "create_all\|time.sleep\|import requests\|float" app/` sin resultados relevantes; todos los handlers son `async def`; ningún `.env` versionado; ninguna credencial en el código.
- [ ] 7.2 Verificar que `ConfigDict(extra="forbid")` está en todos los DTOs de entrada y que `password_hash` no aparece en ningún `Read`.
  - Verificación (`.http`): campo extra en entrada → 422; `GET /usuarios/{id}` sin `password_hash`.

## Workflow follow-up

- C-05 depende de estos DTOs, endpoints y `PaginatedResponse` para construir altas con `UnitOfWork` (transacciones).
- C-06/C-07 dependen de `VentaRepository.get_con_detalle` y de las precargas de relaciones.
- Archivar con `/opsx:archive C-04-contratos-crud` y marcar `[x]` C-04 en `CHANGES.md`.
