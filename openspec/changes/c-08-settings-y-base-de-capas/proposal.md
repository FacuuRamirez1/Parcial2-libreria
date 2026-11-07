# Proposal

## Why

El TP caps 1-4 (implementado, changes C-01..C-07) lee la configuración con `python-dotenv` + `DATABASE_URL` y un `@dataclass Configuracion`, no tiene `Settings` sin secretos por defecto, ni repositorios genéricos, ni `UnitOfWork`, ni paginación por página/tamaño (usa `limit`/`offset`). El `/health/ready` responde siempre 200. El Parcial caps 1-6 (Ejercicio 1, US-101..US-103) exige: `Settings` de pydantic-settings con `POSTGRES_*` y clave JWT/contraseña sin valor por defecto, URL de base con `@computed_field` (`postgresql+asyncpg`), motor y fábrica en el lifespan → `app.state`, `get_session` con `expire_on_commit=False`, hash ficticio de bcrypt calculado una vez al arrancar, `dispose()` al apagar, y `/health/ready` con 503 si la base no contesta. Sin esta base de capas, C-09 (repositorios/UoW por módulo) y C-11 (autenticación) no pueden construirse.

## What Changes

- **`app/core/config.py`**: `Settings` con `pydantic-settings` (`POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `JWT_SECRET_KEY`, `BCRYPT_COST`, `DB_POOL_SIZE`, `COOKIE_SECURE`, `ACCESS_TOKEN_MINUTES`, `SQL_ECHO`); clave JWT y contraseña de base **sin valor por defecto** (la app no arranca si faltan); URL armada con `@computed_field` y driver `postgresql+asyncpg`; reemplaza `python-dotenv`/`DATABASE_URL` del parcial (DD-09, IN-07).
- **`app/core/repository.py`**: `BaseRepository[T]` y `SoftDeleteRepository[T]` genéricos (sesión + clase del modelo; `add`/`update` hacen `flush()`, nunca `commit()`; `SoftDeleteRepository` filtra `borrado_en IS NULL` y agrega `get_by_id_including_deleted` y `soft_delete`).
- **`app/core/unit_of_work.py`**: `UnitOfWork` base (gestor de contexto async: confirma al salir, revierte ante excepción, no cierra la sesión; se abre con `async with`).
- **`app/core/paginacion.py`**: envoltorio genérico `{items,total,page,size,pages}` (solo el contenedor; su uso en listados es C-09); reemplaza `limit`/`offset`.
- **`app/core/database.py`**: motor y fábrica con pool configurable desde `Settings`; `get_session` toma la fábrica de `app.state`, `expire_on_commit=False`, una sesión por petición.
- **`app/main.py`**: `lifespan` calcula una vez el hash ficticio del login, guarda motor/fábrica en `app.state`, hace `dispose()` al apagar; lee `Settings`.
- **`app/modules/health/router.py`**: `GET /health/ready` responde **503** si la base no contesta (IN-09); `/health/live` sin tocar la base.
- **`requirements.txt` / `env.example`**: agregan `pydantic-settings` y `bcrypt`; `env.example` usa `POSTGRES_*` + clave JWT + `SQL_ECHO`, sin secretos.

## Capabilities

### New Capabilities

- `repositorio-base`: `BaseRepository[T]` y `SoftDeleteRepository[T]` genéricos en `app/core/repository.py` (contrato de repositorio sin commit, soft delete por `borrado_en`).
- `unit-of-work`: `UnitOfWork` base en `app/core/unit_of_work.py` (gestor de contexto async, commit/rollback, `async with`, no cierra la sesión).

### Modified Capabilities

- `app-lifecycle`: la configuración pasa de `DATABASE_URL`/`python-dotenv` a `Settings` (pydantic-settings) con `POSTGRES_*`, clave JWT sin default, costo de bcrypt, tamaño de pool, flag `Secure` de la cookie y `@computed_field` con `postgresql+asyncpg`; `get_session` con `expire_on_commit=False`; lifespan con hash ficticio y `dispose()` (DD-09, IN-07, US-102).
- `health`: `GET /health/ready` pasa de 200 siempre a **503** si la base no contesta (`SELECT 1` con tiempo acotado) (IN-09, US-103).

## Impact

- Código nuevo: `app/core/config.py`, `app/core/repository.py`, `app/core/unit_of_work.py`, `app/core/paginacion.py`.
- Código modificado: `app/core/database.py`, `app/main.py`, `app/modules/health/router.py`, `requirements.txt`, `env.example`.
- API: `GET /health/ready` (200 / 503); `/health/live` (200, sin base).
- Base de datos: ninguna (0003/0004 son C-10; no hay `create_all`).
- Dependencias nuevas: `pydantic-settings`, `bcrypt`.
- `paginacion`: `app/core/paginacion.py` se reemplaza de `limit`/`offset` al contenedor genérico `{items,total,page,size,pages}` que ya describe el spec existente `openspec/specs/paginacion/` (no cambia sus requisitos; su uso en listados es C-09).
- No toca módulos de dominio (editoriales, generos, autores, libros, clientes, ventas).
- Cambios posteriores: C-09 usa `BaseRepository`/`UnitOfWork`/`paginacion` en los 7 módulos; C-10 agrega modelos y migraciones; C-11 usa `Settings` (JWT, bcrypt) y el lifespan.

## Open Questions

- Ninguna que bloquee. C-07 es requisito previo (archivado).
