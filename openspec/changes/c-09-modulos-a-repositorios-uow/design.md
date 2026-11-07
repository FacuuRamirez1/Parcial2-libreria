# Design

## Context

Estado actual (observado): los 6 módulos de dominio (`editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`) tienen `models.py`, `schemas.py`, `service.py`, `router.py`; los servicios reciben `SessionDep` y confirman con `session.commit()`; los listados devuelven `list[Read]` con `limit/offset`; no existen `repository.py` ni `unit_of_work.py` a nivel de módulo. `app/core/` provee `config.py`, `database.py` (motor/fábrica/`get_session`/`SessionDep`), `paginacion.py` (hoy `limit/offset`), `errors.py`, `metadata.py`. `BaseRepository[T]`, `SoftDeleteRepository[T]` y `UnitOfWork` son referenciados por C-08; verificar que existan en `app/core/` antes del apply. Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Migrar los 6 módulos a `Router → Service → UnitOfWork → Repository → Model`.
- Servicios reciben `UnitOfWork` (no la sesión), lo abren con `async with`, nunca lo construyen ni confirman.
- Un repositorio por entidad sobre `BaseRepository[T]`; escrituras con `flush()`, `commit`/`rollback` solo en el UoW.
- Precarga (`joinedload` uno a uno, `selectinload` colecciones) declarada dentro del método del repositorio que la necesita; sin carga perezosa.
- Listados `{items,total,page,size,pages}` con `page ≥ 1`, `size` 1–100 (def. 20), página inexistente → 422, `total` con mismos filtros, cero resultados = página vacía.
- Conservar rutas del TP no listadas en el parcial (IN-04) y los códigos 201/404/409/422 con mensajes propios.
- `schemas.py` conserva `extra="forbid"` (entrada) y `exclude_unset` (PATCH); sin `password_hash` en salida.

**Non-Goals:**
- Cambios de esquema o migraciones (C-10/C-13); `libro.borrado_en` no se crea ni se usa (C-09 no inventa la columna).
- Soft delete de `Libro`: `SoftDeleteRepository` se crea en `app/core` pero no se aplica sobre `Libro` en C-09.
- Autenticación, autorización, eventos de seguridad, trigger de solo agregado (C-10..C-13).
- Crear `pytest` ni tests unitarios/e2e (solo `.http` en `test/`).

## Decisions

### D-01 — Capacidades: 7 nuevas, ninguna modificada

Se crean `repositorios-editoriales`, `repositorios-generios`, `repositorios-autores`, `repositorios-libros`, `repositorios-clientes`, `repositorios-ventas` y `unit-of-work-modulos`. Justificación: cada módulo tiene entidad y firmas distintas (libros busca por título/género; ventas detalla con precarga fija), por lo que un spec por módulo es más preciso que uno monolítico; el UoW es un patrón transversal idéntico en todos los módulos, por lo que un solo spec. `paginacion` no se modifica: su spec ya exige `page/size` y `PaginatedResponse[T]`; C-09 solo alinea la implementación (`limit/offset` → `page/size`).

### D-02 — Firmas de repositorios por módulo

Todos heredan `BaseRepository[T]` (constructor `(session, model)`; `get_by_id`, `get_all(offset, limit)`, `count`, `add`, `update`, `delete` con `flush()`). Métodos específicos:
- `editoriales/generios/autores/clientes`: solo genéricos; `clientes` agrega `get_by_email(email)`.
- `libros`: `get_all_filtrado(titulo, genero_id, offset, limit)` con `ILIKE` ligado y `genero_id` opcional; `count_filtrado(titulo, genero_id)`; precarga `joinedload(editorial)` + `joinedload(genero)` en listado/detalle. Sin `soft_delete` (borrado_en no existe).
- `ventas`: `get_con_detalle(id)` con `joinedload(cliente)` + `selectinload(renglones).joinedload(libro)`; `get_all`/`count` con filtro opcional `cliente_id`; precarga de cliente y renglones.

### D-03 — SoftDeleteRepository no se usa sobre Libro en C-09

`SoftDeleteRepository[T]` (filtra `borrado_en IS NULL`, `get_by_id_including_deleted`, `soft_delete`) existe en `app/core` pero ningún módulo lo hereda en C-09. `Libro` se trata como cualquier entidad (`BaseRepository`) hasta C-10/C-13. Esto respeta "no inventar la columna ni usarla sobre Libro".

### D-04 — Construcción y apertura del UnitOfWork

El router expone una dependencia por módulo (p. ej. `get_editoriales_uow(session: SessionDep)`) que instancia `<Modulo>UnitOfWork(session)` y lo devuelve sin abrir; `get_session` es dueño de la sesión y la cierra tras la petición (una sola conexión por petición autenticada). El servicio recibe el UoW, lo abre con `async with uow:` y opera sobre `uow.repositorio_<entidad>` / `uow.session`; las escrituras pasan por `repositorio.add/update/delete` (`flush`); al salir del bloque el UoW confirma o revierte. El servicio nunca llama `session.commit()` ni construye el UoW.

### D-05 — Listados paginados y 422 de página

El servicio obtiene `Paginacion(page, size)` (con propiedades `limit`/`offset` de compatibilidad) desde `get_paginacion`, llama `repositorio.get_all(offset, limit)` y `repositorio.count()`, y arma `PaginatedResponse(items=..., total=..., page=..., size=..., pages=...)`. Si `total > 0` y `page > pages`, responde 422 con mensaje propio ("Página fuera de rango"). `total == 0` → `pages = 1`, `items = []`.

### D-06 — Rutas del TP conservadas (IN-04)

Todas las rutas de `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas` del TP se conservan (incluido `GET /{modulo}/{id}/libros` de editoriales/géneros/autores y `GET /clientes/{id}/perfil`, `GET /clientes/{id}/ventas`), en su grupo actual (abierto/protegido), sin ampliar. Los listados pasan al envoltorio paginado; el resto del comportamiento observable (201/404/409/422, mensajes propios) se mantiene.

### D-07 — app/core no se modifica salvo contrato documentado

`app/core/paginacion.py` debe exponer `page/size` (hoy es `limit/offset`); se documenta como contrato requerido por DD-09 y por el spec existente de `paginacion`. `app/core/repository.py` y `app/core/unit_of_work.py` (`BaseRepository`, `SoftDeleteRepository`, `UnitOfWork`) deben existir (esperados de C-08); verificarlos antes del apply. No se toca `models.py`, `migrations/` ni `alembic.ini`.

## Risks / Trade-offs

- [`app/core/repository.py` / `app/core/unit_of_work.py` ausentes en el snapshot] → Mitigación: verificar existencia antes del apply; crearlos con el contrato de C-08 si faltan, sin alterar firmas.
- [`app/core/paginacion.py` sigue con `limit/offset`] → Mitigación: actualizarlo a `page/size` con propiedades `limit`/`offset` (contrato ya especificado); es el único cambio de `app_core` y está justificado por DD-09.
- [SoftDeleteRepository creado pero inactivo] → Mitigación: documentado explícitamente; C-10 lo aplica sobre `Libro`; no afecta a C-09.
- [Regresión de `.http` existentes] → Mitigación: repetir todos los casos de `test/*.http` del TP contra el refactor más paginación nueva, con respuesta esperada comentada.

## Migration Plan

1. Verificar `app/core/repository.py` y `app/core/unit_of_work.py` (BaseRepository, SoftDeleteRepository, UnitOfWork).
2. Actualizar `app/core/paginacion.py` a contrato `page/size` (compatibilidad `limit`/`offset`).
3. Crear `repository.py` + `unit_of_work.py` en cada uno de los 6 módulos.
4. Refactor `service.py` (UoW, `async with`) y `router.py` (dependencia UoW) de los 6 módulos.
5. Ejecutar `test/*.http` contra `uvicorn app.main:app` con `alembic upgrade head` aplicado; verificar regresión + paginación.
Rollback: revertir los archivos de los 6 módulos y `app/core/paginacion.py`; no hay cambios de base de datos.

## Open Questions

- Ninguna que bloquee los specs. Las preguntas sobre `app_core` (verificación de `repository.py`/`unit_of_work.py` y actualización de `paginacion.py`) se resuelven antes del apply, sin cambiar los specs.
