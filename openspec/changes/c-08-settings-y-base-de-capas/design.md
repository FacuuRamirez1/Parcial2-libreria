# Design

## Context

Estado actual (TP caps 1-4, cambios C-01..C-07 archivados): `app/core/config.py` lee `DATABASE_URL` con `python-dotenv` y un `@dataclass Configuracion`; `app/core/database.py` crea motor/fábrica y `get_session` con `SessionDep` sobre `request.app.state.session_factory`; `app/core/paginacion.py` implementa `limit`/`offset` (NamedTuple `Paginacion`); `app/main.py` tiene `lifespan` que crea motor/fábrica y los guarda en `app.state`; `GET /health/ready` responde siempre 200. No existen `Settings` de pydantic-settings, ni `repository.py`, ni `unit_of_work.py`. Ver `proposal.md - Why` para la motivación completa.

Restricciones que condicionan el diseño:
- Nunca `create_all`; el esquema se crea solo con Alembic (migraciones 0003/0004 son C-10).
- Nunca secretos ni valores por defecto para `JWT_SECRET_KEY` ni `POSTGRES_PASSWORD`: si faltan, la app no arranca.
- Nunca `float` para dinero; `Decimal` / `NUMERIC`.
- Nunca carga perezosa; `joinedload`/`selectinload` dentro del método del repositorio.
- Nunca `commit()` en un repositorio; `add`/`update` hacen `flush()`; confirma solo el Unit of Work.
- `get_session` con `expire_on_commit=False`; motor y fábrica en `app.state` (nunca al importar).
- Todos los handlers `async def`; sin llamadas bloqueantes en handlers.

## Goals / Non-Goals

**Goals:**
- `Settings` (pydantic-settings) con `POSTGRES_*`, `JWT_SECRET_KEY`, `BCRYPT_COST`, `DB_POOL_SIZE`, `COOKIE_SECURE`, `ACCESS_TOKEN_MINUTES`, `SQL_ECHO`.
- URL de base con `@computed_field` + driver `postgresql+asyncpg`.
- Motor y fábrica con pool configurable creados en el lifespan → `app.state`; `dispose()` al apagar.
- Hash ficticio de bcrypt calculado una vez al arrancar (insumo de RN-08).
- `get_session` toma la fábrica de `app.state`, una sesión por petición, `expire_on_commit=False`, se cierra al terminar.
- `BaseRepository[T]` y `SoftDeleteRepository[T]` genéricos (flush sin commit; soft delete por `borrado_en`).
- `UnitOfWork` base (gestor de contexto async: confirma al salir, revierte ante excepción, no cierra la sesión).
- Envoltorio genérico `{items,total,page,size,pages}` en `paginacion.py` (uso en listados es C-09).
- `GET /health/ready` responde 503 si la base no contesta; `/health/live` 200 sin tocar la base.

**Non-Goals:**
- Lógica de transacción por módulo (UoW por módulo con sus repositorios es C-09).
- Uso de la paginación en listados concretos (C-09).
- Modelos nuevos (`usuario`, `asignacion_rol`, `movimiento_stock`, …) y migraciones 0003/0004 (C-10).
- Autenticación, JWT, bcrypt en el bucle, registro/login (C-11).
- `create_all` en cualquier base.

## Decisions

### D-01 — IN-06: `app/main.py` se mantiene (no `main.py` en raíz)
La consigna menciona `main.py`, pero el Dockerfile y el TP usan `app.main:app`. Se conserva `app/main.py` como punto de entrada (SU-07). Alternativa considerada: crear `main.py` en raíz que reexporte `app.main`; descartada por duplicar el punto de entrada y por coincidir con el Dockerfile existente.

### D-02 — IN-07: variables de entorno del parcial
`env.example` y `.env` del parcial usan `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `JWT_SECRET_KEY`, `SQL_ECHO` (sin `DATABASE_URL`). El `despliegue/` del TP (snapshot, C-15) conserva `DATABASE_URL`; son dos proyectos con configuraciones distintas (IN-07). No se mezclan.

### D-03 — Variables de `Settings` y validaciones
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`: sin default para la contraseña; se arman la URL con `@computed_field` (`postgresql+asyncpg://…`).
- `JWT_SECRET_KEY`: sin default; si falta, la app no arranca (NF-02).
- `BCRYPT_COST`: entero con default razonable (p. ej. 12), configurable.
- `DB_POOL_SIZE`: entero con default, configura `pool_size` del motor asincrónico.
- `COOKIE_SECURE`: booleano, configurable (Secure de la cookie `access_token`).
- `ACCESS_TOKEN_MINUTES`: entero con default (p. ej. 30 → 1800 s).
- `SQL_ECHO`: booleano, muestra consultas en consola (NF-07).
- `python-dotenv` se reemplaza por `pydantic-settings`; `DATABASE_URL` deja de leerse en el parcial (DD-09).

### D-04 — `BaseRepository[T]` / `SoftDeleteRepository[T]`
- `BaseRepository[T]` recibe `(session: AsyncSession, model: type[T])` en el constructor (genéricos borrados en runtime).
- Expone al menos `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`.
- `add`/`update` hacen `flush()`, nunca `commit()`.
- `SoftDeleteRepository[T]` hereda de `BaseRepository[T]`, filtra `borrado_en IS NULL` en lecturas y agrega `get_by_id_including_deleted` y `soft_delete` (establece `borrado_en`).
- Cada repositorio de entidad declara su precarga dentro del método que la necesita.

### D-05 — `UnitOfWork`
- Gestor de contexto asincrónico: `async with unit_of_work:`.
- Confirma (`commit`) al salir sin excepción; revierte (`rollback`) ante excepción; no cierra la sesión (no la creó).
- Composición: un UoW por módulo agrupa repositorios sobre la misma sesión.
- El router lo construye mediante una dependencia y se lo pasa al servicio sin abrirlo; el servicio lo abre con `async with` y nunca lo construye.

### D-06 — `paginacion.py` (contenedor, uso en C-09)
- Modelo genérico `{items, total, page, size, pages}`; `page ≥ 1` (def. 1), `size` 1–100 (def. 20); `pages = 1` si `total == 0`, si no `ceil(total / size)`; `page > pages` con `total > 0` → 422.
- Solo el contenedor genérico; su aplicación a los listados de cada módulo es C-09.

### D-07 — `lifespan` y `get_session`
- El lifespan lee `Settings`, crea motor (con `DB_POOL_SIZE`) y fábrica, los guarda en `app.state`, calcula una vez el hash ficticio del login y hace `dispose()` al apagar.
- `get_session` obtiene la fábrica de `app.state`, entrega una sesión por petición con `expire_on_commit=False` y la cierra al terminar.

### D-08 — `GET /health/ready` 503 (IN-09)
- Ejecuta `SELECT 1` con tiempo acotado (≤ 5 s). Responde 200 `{"estado": "listo", "base": "conectada"}` si éxito; 503 si la base no contesta o falla, sin detalles internos. `/health/live` sigue 200 sin tocar la base.

### D-09 — Alcance de C-08 vs C-09
- C-08 toca: `app/core/config.py`, `app/core/database.py`, `app/core/paginacion.py`, `app/core/repository.py`, `app/core/unit_of_work.py`, `app/main.py`, `app/modules/health/router.py`, `requirements.txt`, `env.example`.
- C-09 (no toca C-08): migrar los 7 módulos a repository/UoW/service, usar la paginación en listados, quitar la sesión de los servicios.

### D-09b — Pruebas `.http` (solo artefactos de proponer, sin ejecución de código aquí)
- `test/`: casos de arranque sin variables obligatorias (falla) y `GET /health/ready` 200 / 503. No hay `pytest`.

## Risks / Trade-offs

- [El `despliegue/` del TP conserva `DATABASE_URL` mientras el parcial usa `POSTGRES_*`] → riesgo de confundir las variables; mitigación: documentar la diferencia en ambos `env.example` y `DEPLOY.md` (IN-07).
- [El hash ficticio se calcula una vez al arrancar] → si faltan las variables obligatorias, la app no levanta; es el comportamiento buscado (NF-02), no un defecto.
- [Soft delete solo en `SoftDeleteRepository`, no en `BaseRepository`] → `Libro` usará `SoftDeleteRepository` (C-09); otras entidades usarán `BaseRepository`.

## Migration Plan

No hay cambios de esquema en C-08 (migraciones 0003/0004 son C-10). Rollback: revertir el change; `config.py` vuelve a `python-dotenv`/`DATABASE_URL`, `paginacion.py` a `limit`/`offset`, `health/ready` a 200 siempre, y se quitan `repository.py`/`unit_of_work.py` y las nuevas dependencias.

## Open Questions

- Ninguna que bloquee. Los nombres exactos de variables (`JWT_SECRET_KEY`, `BCRYPT_COST`, `DB_POOL_SIZE`, `COOKIE_SECURE`, `ACCESS_TOKEN_MINUTES`) se declaran aquí y se confirman en la implementación de C-08/C-11.
