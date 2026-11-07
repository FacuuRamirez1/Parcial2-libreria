# Arquitectura Propuesta

> **TP caps 1-4 (implementado)** y **Parcial caps 1-6 (pendiente)**. El Parcial exige una estructura distinta; el TP la tiene hoy sin `repository.py`, `unit_of_work.py`, `security.py`, `dependencies.py` ni módulo `usuarios`.

## Capas (Parcial)

`Router → Service → UnitOfWork → Repository → Model`: cada capa sabe lo suyo y nada más.

| Capa | Responsabilidad | Prohibido |
|---|---|---|
| Router | Rutas HTTP: construye el UoW con una dependencia, llama al servicio y traduce errores a HTTP | Abrir el UoW; reglas de negocio |
| Service | Reglas de negocio; recibe el UoW y lo abre con `async with` | Construir el UoW; recibir la sesión (ya no) |
| UnitOfWork | Gestor de contexto async: confirma al salir, revierte ante excepción; compone los repositorios del módulo con la misma sesión | Cerrar la sesión (no la creó) |
| Repository | Consultas y escrituras de una entidad; precarga declarada dentro del método; `add`/`update` hacen `flush()` | `commit()`; lógica de negocio |
| Model | Tablas, restricciones y relaciones | — |

## Patrones aplicados

| Patrón | Dónde | Por qué | Alcance |
|---|---|---|---|
| Módulo funcional | `app/modules/<módulo>/` | Mismas capas en todos | TP + Parcial |
| Separación tabla / contrato | `models.py` vs `schemas.py` (`extra="forbid"` en entrada) | Nadie se registra con rol ni edita stock por PATCH | TP + Parcial |
| ~~Service con sesión por parámetro~~ | `service.py` | **Reemplazado** por Service con UoW | TP |
| Repository genérico | `core/repository.py`: `BaseRepository[T]`, `SoftDeleteRepository[T]` | Recibe sesión y clase del modelo (los genéricos se borran en runtime) | Parcial |
| Unit of Work | `core/unit_of_work.py` y `modules/<m>/unit_of_work.py` | Varias escrituras en una transacción | Parcial |
| Inyección de dependencias | `get_session`, UoW por módulo, `get_usuario_actual`, `requiere_rol` (misma sesión) | 1 conexión por petición | Parcial |
| Recursos en lifespan | `main.py` + `core/database.py` | Motor/fábrica en `app.state`; hash ficticio; `dispose()` | TP + Parcial |
| Objeto de asociación | `LibroAutor` | `rol` y `orden` | TP |
| Carga anticipada | repositorios | Sin N+1 | TP + Parcial |
| Garantías en la base | UNIQUE, índices únicos parciales, CHECK, FK, trigger | Unicidad, vigencia y solo-agregado | TP + Parcial |
| Borrado lógico | `SoftDeleteRepository` + `Libro.borrado_en` | Las ventas viejas siguen mostrando el libro | Parcial |
| Sesión propia | `intento_acceso` | El intento sobrevive al rollback | Parcial |
| Tarea en segundo plano | alta de venta | `BackgroundTasks` | TP + Parcial |

## Estructura de directorios

### Parcial (pendiente) — estructura obligatoria

```
parcial/  (raíz del proyecto ampliado)
├── main.py  (según la consigna; en el TP vive en app/main.py — ver IN-06)
│                                # aplicación, lifespan y los DOS grupos de rutas (abierto / protegido)
├── seed.py                      # deja la base en el estado inicial conocido (en la consigna: raíz; ver IN-02)
├── app/
│   ├── core/
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # crea motor y fábrica (los llama el lifespan) y get_session
│   │   ├── security.py          # bcrypt fuera del bucle (to_thread + semáforo); emisión/verificación del JWT
│   │   ├── dependencies.py      # usuario actual, roles vigentes, control del cambio obligatorio, requiere_rol
│   │   ├── repository.py        # BaseRepository[T], SoftDeleteRepository[T]
│   │   ├── paginacion.py        # envoltorio {items,total,page,size,pages} y cálculo de páginas
│   │   └── unit_of_work.py      # UnitOfWork base
│   └── modules/
│       ├── health/              # solo router.py
│       ├── usuarios/            # + AsignacionRol, IntentoAcceso, EventoSeguridad
│       ├── editoriales/  generos/  autores/
│       ├── libros/              # + LibroAutor, MovimientoStock
│       ├── clientes/            # + PerfilCliente
│       └── ventas/              # + RenglonVenta
│           └── models.py · schemas.py · repository.py · unit_of_work.py · service.py · router.py
├── migrations/                  # 0001..0004
├── test/                        # archivos .http y solo_agregado.sql
├── alembic.ini · env.example · requirements.txt · README.md
└── evidencia/                   # C-15 (consultas) y C-14 (psql)
```

Cada módulo tiene `models.py` (tablas), `schemas.py` (contratos), `repository.py` (repositorios de sus entidades), `unit_of_work.py` (UoW del módulo), `service.py` (reglas) y `router.py` (HTTP). `health` solo tiene `router.py`.

### TP (implementado) — hoy en el repo

```
app/main.py · app/core/{config,database}.py · app/modules/<7 módulos>/{models,schemas,service,router}.py
scripts/seed.py · migrations/ (0001, 0002) · test/*.http · env.example
```

### Zip de entrega

```
Parcial_Cap1a6_<NombreDelGrupo>.zip
├── parcial/        # arriba, con README.md (integrantes + pasos) y evidencia/
└── despliegue/     # snapshot del TP caps 1-4 (tag de git sobre f1b9b48) + Dockerfile, .dockerignore, env.example (forma de DATABASE_URL), DEPLOY.md, evidencia/ (casos D)
```
Sin `.venv`, `__pycache__` ni `.env`. El despliegue **no** forma parte de la estructura del parcial: se hace sobre el TP, en carpeta aparte.

## Seguridad (Parcial)

- **Contraseñas**: bcrypt con costo en la configuración; toda llamada fuera del bucle (`to_thread`) y bajo semáforo; el hash se calcula antes de abrir la transacción; máx. 72 bytes en el contrato.
- **Token**: JWT firmado (`sub`, `exp`, roles vigentes al emitirlo; claves del entorno). Solo en cookie `access_token` HttpOnly, `SameSite=Lax`, `Max-Age` = duración, `Secure` configurable; nunca en el cuerpo ni leído de `Authorization`.
- **Autorización**: roles vigentes leídos de la base en cada petición; 401 vs 403 siempre diferenciados; dos grupos de rutas con el control de cambio de contraseña montado una vez.
- **Enumeración de cuentas**: mismo mensaje, mismo código y tiempo parecido (hash ficticio); límite de intentos con 429 + `Retry-After`.
- **Validación**: contratos `extra="forbid"`; `Query`/`Path` tipados; ninguna entrada inválida en 500.
- **Inyección SQL**: parámetros ligados siempre.
- **Errores**: mensajes propios; nunca nombres de tablas, restricciones ni trazas.
- **Secretos**: nada en código, `alembic.ini`, repo, imagen ni zip; `.env` no versionado; clave JWT sin default.
- **Auditoría**: `evento_seguridad` (misma transacción que el cambio) e `intento_acceso` (sesión propia).
- **Contenedor** (TP desplegado): usuario sin privilegios, sin secretos en capas, sin `.env` en la imagen, solo el puerto de la app publicado.

## Variables de entorno

### Parcial (`Settings`)

| Variable | Descripción | Sensible |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` / `POSTGRES_HOST` / `POSTGRES_PORT` | Se arma la URL `postgresql+asyncpg://…` con `@computed_field`; **sin default** para contraseña | Contraseña: Sí |
| Clave de firma JWT (nombre a definir en C-08, p. ej. `JWT_SECRET_KEY`) | Secreto de firma; sin default; el README explica cómo generarla | Sí |
| Duración del token, costo de bcrypt, tamaño del pool, `Secure` de la cookie, límites del semáforo | Valores de configuración | No |
| `SQL_ECHO` | Muestra las consultas (NF-07) | No |

### TP (implementado) y despliegue
| Variable | Descripción | Sensible |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://usuario:clave@host:5432/libreria` | Sí |
| `SQL_ECHO` | `false` en el contenedor | No |

> Los dos proyectos usan variables distintas (`POSTGRES_*` vs `DATABASE_URL`); el `despliegue/` no lleva los cambios del parcial. Ver IN-07.

## Entorno

- **Desarrollo**: PostgreSQL 16 local por integrante (`.env` desde `env.example`); sin Docker. Pasos: venv, dependencias, `.env` (con la clave de firma), `alembic upgrade head`, `python seed.py`, uvicorn.
- **Despliegue**: Docker 20.10+ (sin Compose) sobre el VPS; la base es la que provee la cátedra; `docker run … --env-file`. La base no está en `localhost` dentro del contenedor (`host.docker.internal` con `--add-host=host.docker.internal:host-gateway`, o la dirección de la cátedra).
