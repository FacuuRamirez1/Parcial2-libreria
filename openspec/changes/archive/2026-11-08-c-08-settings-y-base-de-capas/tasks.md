# Tasks

> **Verificación**: cada tarea indica cómo se comprueba su finalización en la fase apply. Esta fase es solo proponer artefactos: no se escribe ni modifica código de la aplicación, migraciones, `requirements.txt`, `env.example` ni tests. Referencias: `design.md` (D-01..D-09b) y `specs/`.
> Reglas duras: sin `create_all`; `Decimal`/`NUMERIC` para dinero; nunca `commit()` en un repositorio (solo `flush()`); sin carga perezosa; sin SQL concatenado; sin float para dinero; `get_session` con `expire_on_commit=False`; motor y fábrica en `app.state`; nunca secretos ni valores por defecto para `JWT_SECRET_KEY` ni `POSTGRES_PASSWORD`; listados del parcial `{items,total,page,size,pages}` (uso en listados es C-09). No commitear sin orden del usuario.

## 1. Configuración con Settings (pydantic-settings)

- [x] 1.1 Reescribir `app/core/config.py` con `Settings` de pydantic-settings: `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `JWT_SECRET_KEY`, `BCRYPT_COST`, `DB_POOL_SIZE`, `COOKIE_SECURE`, `ACCESS_TOKEN_MINUTES`, `SQL_ECHO`; `JWT_SECRET_KEY` y `POSTGRES_PASSWORD` sin valor por defecto (la app no arranca si faltan); URL de base con `@computed_field` y driver `postgresql+asyncpg`; eliminar `python-dotenv`/`DATABASE_URL` del parcial (D-02, D-03, specs `app-lifecycle`).
  - Verificación: `app/core/config.py` define `Settings` con `@computed_field` que devuelve `postgresql+asyncpg://…`; sin `python-dotenv` ni `DATABASE_URL`; ningún valor por defecto para `JWT_SECRET_KEY`/`POSTGRES_PASSWORD`.
- [x] 1.2 Verificar que al faltar `JWT_SECRET_KEY` o `POSTGRES_PASSWORD` el arranque falle con mensaje que nombre la variable y sin revelar su valor (specs `app-lifecycle`).
  - Verificación: arrancar la app con cada variable ausente y confirmar error claro que nombra la variable, sin su valor.

## 2. Motor, fábrica y sesión por petición (app/core/database.py)

- [x] 2.1 Ajustar `crear_motor` para recibir el tamaño del pool (`DB_POOL_SIZE`) de `Settings` y crear el motor asincrónico con `pool_size` configurable (D-07, specs `app-lifecycle`).
  - Verificación: `crear_motor(settings)` acepta `DB_POOL_SIZE` y configura el pool del motor.
- [x] 2.2 Ajustar `get_session` para tomar la fábrica de `app.state`, entregar una sesión por petición con `expire_on_commit=False` y cerrarla al terminar (D-07).
  - Verificación: `get_session` usa `request.app.state.session_factory` y `expire_on_commit=False`; la sesión se cierra al finalizar la petición.

## 3. Repositorios genéricos (app/core/repository.py)

- [x] 3.1 Crear `app/core/repository.py` con `BaseRepository[T]`: constructor `(session, model: type[T])`; `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`; `add`/`update` hacen `flush()` y nunca `commit()` (specs `repositorio-base`, D-04).
  - Verificación: el archivo existe, `BaseRepository` es genérico y expone los seis métodos; `add`/`update` llaman a `flush()` y no a `commit()`.
- [x] 3.2 Crear `SoftDeleteRepository[T]` que herede de `BaseRepository[T]`, filtre `borrado_en IS NULL` en `get_by_id`/`get_all`/`count`, y agregue `get_by_id_including_deleted` y `soft_delete` (establece `borrado_en`) (specs `repositorio-base`, D-04).
  - Verificación: `issubclass(SoftDeleteRepository, BaseRepository)` es True; lecturas excluyen `borrado_en` distinto de nulo; `soft_delete` establece `borrado_en`.

## 4. Unit of Work (app/core/unit_of_work.py)

- [x] 4.1 Crear `app/core/unit_of_work.py` con `UnitOfWork` base: gestor de contexto asincrónico (`async with`), confirma al salir sin excepción, revierte ante excepción, no cierra la sesión (no la creó) (specs `unit-of-work`, D-05).
  - Verificación: el archivo existe; `async with uow:` confirma al salir y revierte ante excepción; la sesión no se cierra al salir del bloque.

## 5. Paginación (app/core/paginacion.py)

- [x] 5.1 Reemplazar `app/core/paginacion.py` de `limit`/`offset` por el envoltorio genérico `{items,total,page,size,pages}`: `page ≥ 1` (def. 1), `size` 1–100 (def. 20), `pages = 1` si `total == 0` si no `ceil(total/size)`, `page > pages` con `total > 0` → 422; función `calcular_paginas(total, size)` (specs `paginacion`, D-06).
  - Verificación: `app/core/paginacion.py` define el contenedor genérico y `calcular_paginas`; `calcular_paginas(0, 20) == 1`, `calcular_paginas(25, 10) == 3`.

## 6. Ciclo de vida en el lifespan (app/main.py)

- [x] 6.1 Ajustar el `lifespan` de `app/main.py` para leer `Settings`, crear motor (con `DB_POOL_SIZE`) y fábrica, guardarlos en `app.state`, calcular una vez el hash ficticio del login al arrancar y hacer `dispose()` al apagar (D-07, specs `app-lifecycle`).
  - Verificación: al arrancar, `app.state` tiene motor y fábrica; al apagar se llama `dispose()`; el hash ficticio se calcula una vez.
- [x] 6.2 Confirmar que no se crea motor/fábrica al importar el módulo y que no hay `create_all` (D-01, D-07).
  - Verificación: importar `app.main` no crea motor ni llama `create_all`.

## 7. Health con 503 (app/modules/health/router.py)

- [x] 7.1 Ajustar `GET /health/ready` para ejecutar `SELECT 1` con tiempo acotado (≤ 5 s), responder 200 `{"estado":"listo","base":"conectada"}` si éxito y **503** si la base no contesta o falla, sin detalles internos; `/health/live` sigue 200 sin tocar la base (IN-09, specs `health`, D-08).
  - Verificación: `GET /health/ready` responde 200 con base disponible y 503 con base inaccesible; `GET /health/live` responde 200 sin SQL.

## 8. Dependencias y entorno (requirements.txt, env.example)

- [x] 8.1 Agregar `pydantic-settings` y `bcrypt` a `requirements.txt` con versiones exactas (D-03, specs `app-lifecycle`).
  - Verificación: `requirements.txt` contiene `pydantic-settings` y `bcrypt` con versión exacta.
- [x] 8.2 Reescribir `env.example` con `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, `JWT_SECRET_KEY` y `SQL_ECHO`, sin secretos y sin `DATABASE_URL` (D-03, specs `app-lifecycle`).
  - Verificación: `env.example` tiene las variables `POSTGRES_*`, `JWT_SECRET_KEY` (sin valor real) y `SQL_ECHO`; no tiene `DATABASE_URL` ni contraseñas reales.

## 9. Pruebas .http (test/)

- [x] 9.1 Agregar casos `.http` en `test/`: arranque sin variables obligatorias falla; `GET /health/ready` 200 / 503 (D-09b). Solo archivos `.http`, sin `pytest` (regla dura).
  - Verificación: existen los archivos `.http` con respuesta esperada comentada para arranque sin variables y ready 200/503.

## 10. Chequeo integral de reglas duras

- [x] 10.1 Auditar que no hay `create_all`, `float` para dinero, carga perezosa, SQL concatenado, llamadas bloqueantes en handlers ni `commit()` en repositorios (D-01, reglas duras).
  - Verificación: `grep` sobre `app/` sin hallazgos relevantes; todos los handlers son `async def`.
- [x] 10.2 Confirmar que ningún secreto ni valor por defecto para `JWT_SECRET_KEY` ni `POSTGRES_PASSWORD` está en el código ni en `env.example` (NF-02).
  - Verificación: `env.example` sin secretos; el código no trae `JWT_SECRET_KEY`/`POSTGRES_PASSWORD` por defecto.

## Workflow follow-up

- C-09 usa `BaseRepository`/`UnitOfWork`/`paginacion` en los 7 módulos y quita la sesión de los servicios.
- C-10 agrega modelos nuevos y migraciones 0003/0004.
- C-11 usa `Settings` (JWT, bcrypt) y el hash ficticio del lifespan.
- Archivar con `/opsx:archive C-08-settings-y-base-de-capas` y marcar `[x]` C-08 en `CHANGES.md` solo tras aprobación del usuario.
