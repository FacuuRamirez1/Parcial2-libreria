# Funcionalidades

Organizadas por **épica = ejercicio de la consigna**. Dos bloques: **TP caps 1-4 (implementado, changes C-01..C-07 archivados)** y **Parcial caps 1-6 (pendiente, changes C-08..C-16)**. Las historias del Parcial siguen la numeración US-1NN para no chocar con las del TP.

---

# Bloque A — TP caps 1-4 (implementado)

## Épica 1: Proyecto, conexión y ciclo de vida (10 pts)
### US-001 — Estructura y arranque
- [x] Estructura por módulos; motor y fábrica en el `lifespan` y `app.state`; `get_session` con `expire_on_commit=False`; `DATABASE_URL` en `.env`; `env.example`.
### US-002 — Health
- [x] `live` sin tocar la base; `ready` con `SELECT 1` (siempre 200, estado en el cuerpo).

## Épica 2: Modelos, restricciones y relaciones (25 pts)
### US-003 — Modelos de tabla
- [x] 9 modelos con UNIQUE, CHECK, FK e índices; navegación en ambos extremos; `LibroAutor` como entidad propia; `Cliente.perfil` objeto; dinero `Decimal`. Reglas: TP RN-01, 02, 03, 09.

## Épica 3: Migraciones (10 pts)
### US-004 — Dos migraciones autogeneradas
- [x] 0001 (todo menos `genero`) y 0002 (`genero` + `libro.genero_id`); `upgrade head` y `downgrade -1` + `upgrade head`.

## Épica 4: Contratos y CRUD (15 pts)
### US-005 — CRUD de referencia
- [x] DTO separados; PATCH con `exclude_unset`; 201/404/409/422; listados `limit`/`offset`; búsqueda por título con parámetros ligados.

## Épica 5: Altas con relaciones (20 pts)
### US-006 — Alta de libro con autores · US-007 — Perfil del cliente · US-008 — Alta de venta con renglones
- [x] Sin pre-consultas de ids; 409 con mensaje propio; precio copiado, total calculado por el servidor; perfil único (409).

## Épica 6: Lecturas sin N+1 (10 pts)
### US-009 — Detalles con carga anticipada
- [x] `joinedload`/`selectinload` en la misma consulta; número fijo de consultas.

## Épica 7: Asincronía sin bloqueos (10 pts)
### US-010 — Aviso de comprobante en segundo plano
- [x] `BackgroundTasks` + `asyncio.sleep(0.5)` + log.

---

# Bloque B — Parcial caps 1-6 (pendiente)

Mapa épica → change: Ej.1→C-08, Ej.2→C-10, Ej.3 y 6 y 8→C-09/C-13, Ej.4→C-11, Ej.5→C-12, Ej.7→C-10/C-11, Ej.9→C-15, Ej.10→C-16, casos/seed/evidencia→C-14.

## Épica P1: Proyecto, configuración y ciclo de vida (6 pts) — C-08

### US-101 — Settings sin secretos por defecto
**Como** desarrollador **quiero** `Settings` (pydantic-settings) **para** configurar el sistema desde el entorno.
- [ ] Variables `POSTGRES_USER/PASSWORD/DB/HOST/PORT`, clave JWT, pool, costo de bcrypt, duración del token, `Secure` de la cookie, `SQL_ECHO`.
- [ ] La URL se arma con `@computed_field` con driver `postgresql+asyncpg`.
- [ ] Sin valor por defecto para la clave JWT ni la contraseña de la base: si faltan, la app no arranca.
- [ ] `env.example` completo y sin secretos.

### US-102 — Lifespan y sesión
- [ ] Motor (con pool declarado en la configuración) y fábrica en el lifespan → `app.state`; no al importar.
- [ ] `get_session` toma la fábrica de `app.state`, una sesión por petición, `expire_on_commit=False`, la cierra al terminar.
- [ ] El lifespan calcula una vez el hash ficticio del login y hace `dispose()` al apagar.

### US-103 — Health con 503
- [ ] `GET /health/live` sin tocar la base; `GET /health/ready` con `SELECT 1` y **503** si la base no contesta.

## Épica P2: Modelos, relaciones y migraciones (10 pts) — C-10

### US-104 — Modelos nuevos y cambios
- [ ] `Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad` (módulo `usuarios`), `MovimientoStock` (módulo `libros`); `Cliente.usuario_id` y `Libro.borrado_en`.
- [ ] Dos índices únicos parciales con `postgresql_where` (asignación abierta y ISBN vigente); `Cliente.usuario` devuelve un objeto.
### US-105 — Migraciones 0003 y 0004
- [ ] 0003 autogenerada, leída, con comentario; 0004 con trigger de solo agregado a mano; `upgrade head` / `downgrade base` / `upgrade head`.

## Épica P3: Contratos y CRUD (8 pts) — C-09/C-13

### US-106 — Contratos estrictos y envoltorio
- [ ] DTO de entrada con `extra="forbid"`; ninguna respuesta con `password_hash`; PATCH con `exclude_unset`.
- [ ] Códigos 201/204/404/409/422; listados con `{items,total,page,size,pages}` y 422 si la página no existe.
- [ ] Búsqueda de libros por título con parámetros ligados, sin distinguir mayúsculas.

## Épica P4: Autenticación (14 pts) — C-11

### US-107 — Registro (RN-02, RN-01)
- [ ] `POST /auth/registro` crea usuario + rol CLIENTE + ficha de cliente en un solo UoW; correo repetido (de usuario o de cliente) → 409 y sin filas sueltas.
### US-108 — Login
- [ ] Orden: límite (429 + `Retry-After`) → verificación contra hash real o ficticio; cookie `access_token` (HttpOnly, SameSite=Lax, Max-Age, Secure configurable); cuerpo `{mensaje, debe_cambiar_password, expira_en_segundos}` sin token.
- [ ] JWT con `sub`, `exp` y roles vigentes al emitirlo; cada intento se anota en `intento_acceso` desde sesión propia.
- [ ] bcrypt en `to_thread` bajo semáforo; hash antes de abrir la transacción; máx. 72 bytes → 422.
### US-109 — Cierre de sesión, `/auth/yo` y cambio de contraseña
- [ ] `POST /auth/logout` borra la cookie; `GET /auth/yo` devuelve usuario, roles vigentes y los del token; `POST /auth/cambiar-password` deja `debe_cambiar_password=false` y la misma cookie sigue sirviendo; deja evento de seguridad.

## Épica P5: Autorización (12 pts) — C-12

### US-110 — Usuario actual y roles vigentes
- [ ] `get_usuario_actual` → 401 (sin cookie, token inválido/vencido, usuario inexistente o inactivo); `requiere_rol` → 403 consultando la base en cada petición; comparten la sesión con el UoW.
### US-111 — Administración de roles
- [ ] ADMIN asigna roles con vencimiento opcional (con zona y futuro, si no 422) y los revoca sin borrar la fila; reasignar un vencido cierra la anterior y abre otra; autoprotección (RN-05, 409); alta de personal con contraseña provisoria (`debe_cambiar_password`); `GET /eventos`.
### US-112 — Dos grupos de rutas y lo propio
- [ ] Grupo abierto y grupo protegido con el control de cambio obligatorio montado una vez (403 hasta cambiar); `/mis-ventas` y `GET /ventas/{id}` decidido por el servicio (personal o dueño, si no 403).

## Épica P6: Repositorios y Unit of Work (16 pts) — C-09 (refactor) / C-13

### US-113 — Jerarquías de repositorios
- [ ] `BaseRepository[T]` (sesión + clase del modelo; `get_by_id`, `get_all`, `count`, `add`, `update`, `delete`) y `SoftDeleteRepository[T]` (filtra dados de baja; `get_by_id_including_deleted`, `soft_delete`); `add`/`update` hacen `flush()`, nunca `commit()`; un repositorio por entidad con precarga dentro del método.
### US-114 — UnitOfWork
- [ ] `UnitOfWork` base como gestor de contexto async (confirma al salir, revierte ante excepción, no cierra la sesión); un UoW por módulo con sus repositorios sobre la misma sesión; el router lo construye por dependencia, el servicio lo abre con `async with` y nunca lo construye.
- [ ] RN-02, RN-10 y RN-16 cada una en un solo bloque. Migrar los 7 módulos del TP y quitar la sesión de los servicios.

## Épica P7: Integridad: solo agregado e intento de acceso (10 pts) — C-10/C-11

### US-115 — Trigger de solo agregado
- [ ] UPDATE/DELETE sobre `movimiento_stock` rechazados por el trigger, desde psql incluido (`test/solo_agregado.sql`, caso C-14).
### US-116 — Intento de acceso en sesión propia
- [ ] Sesión y transacción propias, siempre confirmadas, con el comentario de las tres cosas (qué hace distinto, por qué, costo).

## Épica P8: Lecturas sin N+1 y asincronía (6 pts) — C-09/C-13

### US-117 — Detalle de venta fijo en consultas
- [ ] Venta con cliente, renglones y libro de cada renglón (incluso dado de baja) con carga anticipada declarada en el repositorio; consultas independientes de la cantidad de renglones (C-15).
### US-118 — Aviso en segundo plano visible
- [ ] `BackgroundTasks` (`sleep(0.5)` + log) solo si se confirmó; el mensaje se ve con el arranque normal de uvicorn (configurar el logger).

## Épica P9: Stock por movimientos, baja lógica y ventas — C-13

### US-119 — Alta con stock inicial y reposición
- [ ] `POST /libros` con `stock_inicial` deja el movimiento "Stock inicial"; `POST /libros/{id}/reponer` (ADMIN, 200) deja su movimiento; `GET /libros/{id}/movimientos` (ADMIN); PATCH sin stock (422).
### US-120 — Baja lógica y re-alta de ISBN
- [ ] `DELETE /libros/{id}` → 204; no aparece en el catálogo; no se vende ni repone (409); el mismo ISBN puede volver a cargarse (201); segundo vigente → 409; ventas viejas siguen mostrando el título.
### US-121 — Venta con descuento atómico
- [ ] `POST /ventas`: venta + renglones + descuento + un movimiento por renglón en una sola transacción; cliente o libro inexistente o libro dado de baja → 409; stock insuficiente → 409 sin escrituras; punto único de escritura del stock.

## Épica P10: Seed, casos y evidencia — C-14
### US-122 — Datos iniciales y casos
- [ ] `seed.py` (vacía y carga los datos del Parcial, con evento `SISTEMA`); `test/*.http` con casos C-01..C-16 y resultado esperado en comentario (sesiones múltiples con `# @name`, `# @no-cookie-jar` y `Cookie: {{loginAdmin.response.headers.Set-Cookie}}`); `test/solo_agregado.sql`; README con integrantes y pasos desde cero (venv, dependencias, `.env` con cómo generar la clave de firma, `alembic upgrade head`, `python seed.py`, servidor); `evidencia/` con C-15 (2 y 4 renglones) y captura psql de C-14.

## Épica P11: Contenedor: la imagen (11 pts) — C-15
### US-123 — Dockerfile del TP caps 1-4
- [ ] Sobre un snapshot del TP (tag de git sobre `f1b9b48`) copiado a `despliegue/`; solo se agregan `Dockerfile` y `.dockerignore` (más `env.example` y `DEPLOY.md`); su lógica no se toca (salvo defecto propio, anotado en DEPLOY.md).
- [ ] `FROM python:3.12-alpine`; copiar e instalar `requirements.txt` con `--no-cache-dir` antes del código; usuario sin privilegios con `USER`; `.dockerignore` excluye `.env`, `.venv`, `.git`, `__pycache__`; sin secretos en la imagen; al arrancar `alembic upgrade head` y luego uvicorn `app.main:app` en `0.0.0.0`; `HEALTHCHECK` sobre `/health/ready` con **127.0.0.1** (no `localhost`; Alpine solo trae `wget`).
- [ ] Ejecución: `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> libreria`.

## Épica P12: Despliegue en el VPS (7 pts) — C-16
### US-124 — TP en línea
- [ ] Imagen construida en el servidor (o llevada); `docker run` con la base de la cátedra (`DATABASE_URL`, `SQL_ECHO=false`; la base no está en `localhost`: `host.docker.internal` + `--add-host=host.docker.internal:host-gateway`, o la dirección que entregue la cátedra); datos cargados con `docker exec libreria …`; sigue en línea hasta las notas.
- [ ] `DEPLOY.md`: URL pública, día y hora, comandos `docker build` y `docker run` completos (con el nombre del archivo de variables, sin su contenido), cambios hechos al TP, cómo se actualiza (rebuild → `docker rm -f` → `docker run`).
- [ ] `evidencia/` con la salida de los casos D-01..D-08.

## Entregables transversales (Parcial)
- Zip `Parcial_Cap1a6_<NombreDelGrupo>.zip` con `parcial/` y `despliegue/` (ver `01_vision_y_objetivos.md`), sin `.venv`, `__pycache__` ni `.env`.
