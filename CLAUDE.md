# Parcial2-libreria — Instrucciones para Agentes

> Este archivo (y su copia `AGENTS.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.
> **Alcance**: el repo contiene el TP de los capítulos 1-4 (implementado, C-01..C-07) y el **Parcial caps 1-6** (C-08..C-16). La consigna vigente es `Parcial_Cap1a6_Consigna.pdf` (texto en `docs/Parcial_Cap1a6_Consigna.txt`); la del TP original era `TP_Cap1a4_Consigna.pdf`.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima |
|------|------------|----------------|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI (todos los handlers `async def`) | 0.111 |
| Modelos y contratos | SQLModel | 0.0.24 |
| ORM / motor / sesión | SQLAlchemy asincrónico | 2.0 |
| Driver | asyncpg | 0.30 |
| Base de datos | PostgreSQL | 16 |
| Migraciones | Alembic (plantilla asincrónica) | 1.13 |
| Configuración | pydantic-settings (`Settings`, sin secretos por defecto) | 2.0 |
| Hash de contraseñas | bcrypt | 4.0 |
| Token | PyJWT (JWT en cookie HttpOnly) | 2.8 |
| Servidor ASGI | uvicorn (el de `fastapi[standard]`) | — |
| Contenedor (solo `despliegue/`) | Docker, imagen base `python:3.12-alpine` | 20.10 |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.** Cada sección distingue "TP caps 1-4 (implementado)" de "Parcial (pendiente)".

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Propósito, alcance y los 10 ejercicios del parcial |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | ADMIN / VENDEDOR / CLIENTE, grupos de rutas abierto/protegido, matriz de endpoints |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Tablas, restricciones, índices únicos parciales, trigger, migraciones 0001-0004, seed |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | RN-01..RN-16 del parcial, requisitos no funcionales |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Registro, login, revocación, venta con stock, reposición, baja y re-alta de ISBN, Docker |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Capas Router→Service→UoW→Repository→Model, estructura, variables de entorno |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | DD-01…16 y SU-01…13 (las del TP superadas están marcadas) |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Ambigüedades de la consigna (tabla de endpoints con columnas entrelazadas, `seed.py`, datos del VPS) a resolver en cada propose |

> Los códigos y roles marcados `(*)` en la KB son inferidos de una tabla ilegible del PDF: confirmarlos contra `docs/Parcial_Cap1a6_Consigna.txt` en cada `/opsx:propose`.

---

## Skills Disponibles

Instaladas a nivel proyecto en `.claude/skills/`.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI, módulos router/service/schemas, lifespan, async, auth (JWT/bcrypt) y dependencias | `fastapi`, `fastapi-templates`, `fastapi-expert`, `backend-development`, `python-backend` |
| **Datos y Migraciones** | Modelos SQLModel, restricciones, Alembic, repositorios/UoW, carga anticipada | `sqlmodel`, `postgresql-table-design`, `database-patterns`, `python-backend` |
| **Despliegue** | Dockerfile, imagen alpine, HEALTHCHECK, `.dockerignore`, `docker run` (C-15/C-16, solo `despliegue/`) | `docker-best-practices` |
| **Orquestación** | OPSX / documentación / roadmap | `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-creator` |

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.
> `fastapi-templates` sugiere repositorios/Unit of Work: **desde el parcial SÍ se usan** (C-08/C-09), con las reglas de más abajo. No hay skill específica de bcrypt/PyJWT, RBAC ni repositorios/UoW (`fastapi-expert` y `backend-development` cubren auth solo en general): se resuelve con la KB, la consigna y context7. `docker-best-practices` sugiere multi-stage y Compose: la consigna pide `python:3.12-alpine` y prohíbe Compose, así que prevalece la consigna.

---

## Roadmap de Changes

El plan completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 16 changes. C-01..C-07 (TP caps 1-4) archivados e **intactos**; C-08..C-16 (parcial) pendientes.
- **Regla de conexión**: lo ya implementado no se rehace; solo se modifica donde haga falta conectarlo con lo nuevo (cada change nuevo lista en "Conecta con" qué archivos de C-01..C-07 toca).
- **Camino crítico**: `C-08 → C-09 / C-10 (paralelo) → C-11 → C-12 → C-13 → C-14`.
- **Rama independiente** (Docker, sobre el snapshot del TP): `C-15 → C-16`, puede arrancar desde ya.
- **Próximos changes**: `C-08` (`settings-y-base-de-capas`) y `C-15` (`imagen-docker-tp-cap1a4`).
- **Snapshot del TP**: antes de C-15, marcar con un tag de git el commit `f1b9b48` y copiarlo a `despliegue/`.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** + las universales que el global no cubre.
> **Ámbito**: las reglas de abajo rigen para `app/` (el parcial). Las del TP caps 1-4 que el parcial supera están en la sección "Snapshot `despliegue/`".

### Datos y base
- NUNCA `create_all` → el esquema se crea únicamente con Alembic (`alembic upgrade head`).
- NUNCA `float` para dinero → `Decimal` en Python y `NUMERIC(10,2)` / `NUMERIC(12,2)` en la base.
- NUNCA pre-consultar unicidad o existencia de ids → escribir y dejar que UNIQUE / FK rechacen; responder 409. (Excepción de la consigna, RN-05: la asignación de rol abierta duplicada se comprueba en el servicio, con el índice único parcial como garante.)
- NUNCA devolver texto interno de la base (tablas, restricciones, trazas) → traducir `IntegrityError` a un mensaje propio; ninguna entrada inválida termina en un 500.
- NUNCA renombrar ni quitar tablas o columnas de la consigna → solo se pueden agregar columnas.

### Lecturas y async
- NUNCA carga perezosa → `joinedload` (relaciones a uno) y `selectinload` (colecciones), declarados **dentro del método del repositorio** que los necesita.
- NUNCA llamadas bloqueantes en handlers (`time.sleep`, `requests`, acceso síncrono a la base, bcrypt) → todo `async def`.
- NUNCA SQL armado por concatenación con datos del usuario → parámetros ligados.
- Los listados responden `{items, total, page, size, pages}`: `page` ≥ 1, `size` 1–100 (def. 20), página inexistente → 422, `total` cuenta con los mismos filtros; con cero resultados hay una página vacía.

### Capas, repositorios y Unit of Work
- Capas: `Router → Service → UnitOfWork → Repository → Model`; cada capa sabe lo suyo y nada más. Cada módulo tiene `models.py`, `schemas.py`, `repository.py`, `unit_of_work.py`, `service.py`, `router.py`.
- NUNCA `commit()` en un repositorio → `add`/`update` hacen `flush()`; confirma solo el Unit of Work al salir del bloque, y revierte si sale con excepción.
- NUNCA que el servicio construya su Unit of Work → el router lo construye con una dependencia y lo pasa sin abrir; el servicio lo abre con `async with`.
- NUNCA que el Unit of Work cierre la sesión → no la creó; la cierra `get_session`.
- `BaseRepository[T]` recibe la sesión y la clase del modelo (los genéricos se borran en runtime); `SoftDeleteRepository[T]` hereda de él, lo usa `Libro`, filtra los dados de baja y agrega `get_by_id_including_deleted` y `soft_delete`.
- NUNCA dos conexiones por petición autenticada → `get_usuario_actual` y `requiere_rol` reciben la **misma sesión** que el Unit of Work.
- NUNCA escribir `libro.stock` fuera de un único punto del código (movimiento) → lo usan el alta del libro, la reposición y el registro de ventas. Siempre `stock == suma(movimientos)`.
- Las operaciones de varias escrituras (registro RN-02, venta/stock RN-10, eventos de seguridad RN-16) se escriben cada una en **un solo bloque** de Unit of Work.
- Ciclo de vida: motor y fábrica de sesiones se crean en el `lifespan` y se guardan en `app.state` (nunca al importar un módulo); `get_session` usa `expire_on_commit=False`; el `lifespan` calcula una vez el hash ficticio del login y hace `dispose()` al apagar.

### Autenticación, autorización y secretos
- NUNCA un valor por defecto para la clave de firma del JWT ni para la contraseña de la base → si faltan, la aplicación no arranca. NUNCA credenciales en el código, en `alembic.ini` ni en el repo; `env.example` sin secretos.
- La configuración sale de `Settings` (pydantic-settings); la URL de la base se arma con `POSTGRES_USER/PASSWORD/DB/HOST/PORT` (driver `postgresql+asyncpg`) en un `@computed_field`; costo de bcrypt, pool y Secure de la cookie son configuración.
- NUNCA bcrypt en el bucle de eventos → `to_thread` bajo un semáforo; y NUNCA calcular el hash dentro de la transacción (se calcula antes de abrir el UoW).
- NUNCA aceptar más de 72 **bytes** en un campo que termina en bcrypt (contraseña, login, actual del cambio) → límite en el contrato (422, no 500).
- NUNCA el token fuera de la cookie `access_token` (HttpOnly, SameSite=Lax, Max-Age = duración del token, Secure configurable) → ni en el cuerpo ni leído de `Authorization`.
- NUNCA decidir permisos con los roles del token → `requiere_rol` consulta en la base los roles **vigentes** (no revocados, sin vencer) en cada petición; los del token son informativos.
- SIEMPRE distinguir 401 (sin sesión, token inválido/vencido, usuario inexistente o inactivo) de 403 (sin permiso o cambio de contraseña pendiente).
- Login: primero el límite de intentos (429 + `Retry-After`, sin calcular hash), después la verificación contra el hash del usuario o un hash ficticio; mismo mensaje y tiempo parecido exista o no el correo.
- El cambio obligatorio de contraseña se monta **una sola vez** con dos grupos de rutas en `main.py` (abierto y protegido): FastAPI suma dependencias y no las resta.
- Autoprotección: un administrador no se revoca su propio ADMIN y el sistema nunca queda sin administradores vigentes. Revocar escribe `revocada_en`; la fila no se borra.
- Los contratos de entrada llevan `extra="forbid"`; ninguna respuesta incluye `password_hash`.

### Integridad y esquema (parcial)
- `movimiento_stock` es de solo agregado: NUNCA `UPDATE`/`DELETE` → lo impone el trigger de la migración 0004 (escrita a mano). El stock no se edita por PATCH.
- NUNCA que `intento_acceso` comparta transacción con su petición → se escribe en sesión y transacción **propias**, siempre confirmadas, con un comentario que diga qué hace distinto, por qué no puede compartirla y su costo (deja filas aunque la petición falle).
- Cada alta de personal, cambio de rol y cambio de contraseña deja una línea en `evento_seguridad` en la **misma** transacción (los datos iniciales, con actor `SISTEMA`, texto y no usuario).
- Borrado lógico de `libro` (`borrado_en`): el ISBN es único solo entre vigentes (índice único parcial `WHERE borrado_en IS NULL`); un libro dado de baja no se vende ni repone, pero las ventas viejas lo siguen mostrando.
- Migraciones: las dos del TP más dos nuevas. La 0003 con `--autogenerate`, la 0004 a mano; cada nueva se lee antes de aplicarla y lleva un comentario que lo diga. `upgrade head` → `downgrade base` → `upgrade head` debe funcionar. Cada FK nueva lleva índice. Fechas nuevas `timestamptz`.
- `seed.py` vacía las tablas y carga los datos iniciales de la consigna; `stock` coincide con la suma de movimientos en los cinco libros.

### Alcance y proyecto
- Fuera de alcance: concurrencia/bloqueos (cap. 7), Redis y colas (cap. 8) → el aviso del comprobante es `BackgroundTasks` (`asyncio.sleep(0.5)` + log visible con uvicorn normal), solo si la operación se confirmó.
- NUNCA crear changes fuera de los 16 de `CHANGES.md`.
- NUNCA exponer rutas fuera de la tabla de endpoints de la consigna del parcial (más los `PATCH`/`GET` de apoyo del TP ya existentes que se conserven según IN-04).
- Pruebas: archivos `.http` en `test/` con la respuesta esperada comentada (casos C-01..C-16) y `test/solo_agregado.sql`; antes de cada archivo se corre `python seed.py`.

### Snapshot `despliegue/` (TP caps 1-4 tal como se entregó)
- Es el TP **sin** los cambios del parcial: NUNCA llevarle repositorios, Unit of Work, auth, borrado lógico, movimientos de stock ni `Settings`; sigue con `DATABASE_URL`, `limit`/`offset` y `GET /health/ready` según su propia consigna.
- Solo se le agregan `Dockerfile`, `.dockerignore`, `env.example` y `DEPLOY.md`; su lógica no se toca salvo un defecto propio, que se corrige y se anota en `DEPLOY.md`.
- Imagen base `python:3.12-alpine`; `requirements.txt` instalado con `--no-cache-dir` **antes** de copiar el código; la app NO corre como root (`USER`); `.dockerignore` excluye `.env`, `.venv`, `.git` y `__pycache__`.
- NUNCA secretos en la imagen (ni `DATABASE_URL` en el Dockerfile) → entran con `--env-file` al `docker run`. NUNCA Docker Compose.
- El contenedor ejecuta `alembic upgrade head` y luego `uvicorn app.main:app --host 0.0.0.0`; `HEALTHCHECK` sobre `http://127.0.0.1:8000/health/ready` (no `localhost`: wget resuelve a `::1`). Desde el contenedor la base no está en `localhost` (`host.docker.internal` + `--add-host=host.docker.internal:host-gateway`).
- Reglas del TP que siguen valiendo ahí: sin `create_all`, sin float para dinero, sin carga perezosa, sin SQL concatenado, un change por ejercicio del TP original.

### Universales (no cubiertas por el global)
- NUNCA buildear ni commitear sin que el usuario lo pida → esperar la orden explícita.
- Commits convencionales (`feat:`, `fix:`, `chore:`, `docs:`…).
- El `.zip` de entrega no lleva `.venv`, `__pycache__` ni `.env`.

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen; ante conflicto entre la KB y la consigna del parcial, prevalece la consigna.
