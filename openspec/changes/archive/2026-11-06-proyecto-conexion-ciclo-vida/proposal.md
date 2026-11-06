# Proposal

## Why

El repositorio no tiene código: antes de modelar tablas (C-02), migrar (C-03) o exponer CRUD (C-04+) hace falta una base común que arranque, se conecte a PostgreSQL 16 de forma asincrónica y administre bien el ciclo de vida del motor y de las sesiones. Es el Ejercicio 1 de la consigna (10 pts; US-001, US-002) y el criterio de evaluación mira "estructura, lifespan, `Depends`, `.env` y `env.example"`; además, un proyecto que no levanta o que contiene credenciales no se corrige.

## What Changes

- Estructura obligatoria: `app/main.py`, `app/core/config.py`, `app/core/database.py` y los 7 módulos (`health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`) bajo `app/modules/`, cada uno con `models.py`, `schemas.py`, `service.py` y `router.py` importables (vacíos salvo `health`).
- Configuración leída del entorno con `python-dotenv`: `DATABASE_URL` (obligatoria, driver `postgresql+asyncpg`) y `SQL_ECHO` (opcional, `false` por defecto) que controla el `echo` del motor.
- `lifespan` de la aplicación: crea el motor asincrónico (asyncpg) y la fábrica de sesiones, los guarda en `app.state` y llama a `engine.dispose()` al apagar.
- Dependencia `get_session` inyectada con `Depends` (alias `SessionDep`): una sesión por petición, creada con `expire_on_commit=False`, cerrada al terminar la petición.
- Endpoints de salud: `GET /health/live` → `200 {"estado": "vivo"}` sin tocar la base; `GET /health/ready` → ejecuta `SELECT 1` y devuelve el estado de la base (200 si responde, 503 con mensaje propio si no).
- Archivos de proyecto: `env.example` sin secretos, `requirements.txt` con versiones fijadas (`==`), `pyproject.toml` con el entrypoint de FastAPI, y un `README.md` mínimo de arranque (se completa en C-07).
- Verificación sólo con `.http` (como exige la consigna): `test/health.http` con las respuestas esperadas comentadas, más comprobaciones manuales de arranque, `SQL_ECHO` y cierre del motor.
- Sin `create_all`, sin credenciales en el repo. `.gitignore` ya existe e ignora `.env`: no se recrea.

Fuera de alcance: tests automatizados (la consigna pide sólo `.http`), modelos/tablas reales (C-02), Alembic y `scripts/seed.py` (C-03), CRUD y handler global de `IntegrityError` (C-04), autenticación, repositorios/UoW, Redis, Docker.

## Capabilities

### New Capabilities
- `app-lifecycle`: configuración por entorno, creación y cierre del motor asincrónico en el `lifespan`, fábrica de sesiones en `app.state`, sesión por petición vía `Depends` y garantías de proyecto (estructura de módulos, sin `create_all`, sin credenciales versionadas).
- `health`: sondas de disponibilidad de la API (`/health/live`) y de la base de datos (`/health/ready`), con su contrato de respuesta.

### Modified Capabilities
<!-- Ninguna: openspec/specs/ está vacío (proyecto nuevo). -->

## Impact

- **Código nuevo**: `app/` completo (paquetes `core` y `modules/*`), `test/` (archivos `.http`).
- **API**: dos endpoints nuevos bajo `/health`.
- **Dependencias**: `fastapi[standard]`, `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg`, `python-dotenv` (runtime). Sin dependencias de desarrollo.
- **Entorno**: cada integrante necesita PostgreSQL 16 local y su `.env` (DD-03); `/health/ready` devuelve 503 si no hay conexión.
- **Changes posteriores**: C-02..C-07 se apoyan en `SessionDep`, en la estructura de módulos y en `SQL_ECHO` (evidencia de C-06).
