# Descripción General

> **TP caps 1-4 (implementado)** y **Parcial caps 1-6 (pendiente)**. Lo marcado "Parcial" reemplaza o agrega a lo del TP.

## Stack tecnológico

| Capa | Tecnología | Versión mínima | Alcance |
|---|---|---|---|
| Lenguaje | Python | 3.12 | TP + Parcial |
| Framework web | FastAPI (todos los handlers `async def`) | 0.111 | TP + Parcial |
| Modelos y contratos | SQLModel | 0.0.24 | TP + Parcial |
| ORM / motor / sesión | SQLAlchemy asincrónico | 2.0 | TP + Parcial |
| Driver | asyncpg | 0.30 | TP + Parcial |
| Base de datos | PostgreSQL | 16 | TP + Parcial (en el VPS, la que provee la cátedra) |
| Migraciones | Alembic (plantilla asincrónica) | 1.13 | TP + Parcial |
| Configuración | python-dotenv (TP) → **pydantic-settings** (Parcial) | 1.0 → 2.0 | TP: `DATABASE_URL`; Parcial: `Settings` |
| Hash de contraseñas | **bcrypt** | 4.0 | Parcial |
| Token | **PyJWT** | 2.8 | Parcial |
| Servidor ASGI | uvicorn (el de `fastapi[standard]`) | — | TP + Parcial |
| Contenedor | **Docker** (imagen `python:3.12-alpine`) | 20.10 | Solo el despliegue del TP |

### Configuración
- **TP (implementado)**: `DATABASE_URL` en `.env`; `SQL_ECHO` opcional. `env.example` sin secretos.
- **Parcial (pendiente)**: clase `Settings` (pydantic-settings) desde el entorno o un `.env` no versionado. La URL se arma con un `@computed_field` a partir de `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`, con driver `postgresql+asyncpg`. La **clave de firma JWT** también sale del entorno. Ni la clave ni la contraseña de la base tienen valor por defecto: si faltan, la app no arranca. También se declaran en la configuración: tamaño del pool, costo de bcrypt y duración del token. `env.example` con todas las variables y ningún secreto.
- **Despliegue (TP en el contenedor)**: sigue con `DATABASE_URL` y `SQL_ECHO=false` vía `--env-file`.

## Arquitectura general

**TP (implementado)** — por módulo funcional (`models.py`, `schemas.py`, `service.py`, `router.py`); el service recibe la sesión:

```
Cliente HTTP → router.py → (Depends(get_session)) → service.py → SQLModel/SQLAlchemy async → asyncpg → PostgreSQL 16
```

**Parcial (pendiente)** — capas **Router → Service → UoW → Repository → Model**; los servicios dejan de recibir la sesión:

```
Cliente HTTP
   │  cookie access_token
   ▼
router.py      construye el UnitOfWork vía Depends, llama al service, traduce errores a HTTP
   │  Depends(get_session) compartida con get_usuario_actual / requiere_rol (1 conexión por petición)
   ▼
service.py     reglas de negocio; recibe el UoW SIN abrir; lo abre con `async with`; nunca lo construye
   ▼
unit_of_work.py  UnitOfWork base (gestor de contexto async): commit al salir, rollback ante excepción; NO cierra la sesión
   ▼
repository.py  BaseRepository[T] / SoftDeleteRepository[T]: flush(), nunca commit(); precarga declarada en el método
   ▼
models.py      SQLModel + restricciones ──► asyncpg ──► PostgreSQL 16
```

Excepción deliberada: `intento_acceso` se escribe desde **otra sesión y otra transacción** que se confirman siempre (sección 6.8.1 de la consigna).

Ciclo de vida (TP y Parcial): el motor asincrónico y la fábrica de sesiones se crean en el `lifespan` (funciones de `core/database.py`), se guardan en `app.state` y el motor se cierra con `dispose()` al apagar. Sesiones con `expire_on_commit=False`. Parcial: el lifespan calcula además, una vez, el hash ficticio del login.

## Integraciones externas

| Servicio | Propósito | Tipo | Alcance |
|---|---|---|---|
| PostgreSQL 16 | Persistencia | asyncpg | TP + Parcial |
| Aviso de comprobante (simulado) | Notificar tras una venta | `BackgroundTasks` + `await asyncio.sleep(0.5)` + log visible con el arranque normal de uvicorn | TP + Parcial; corre solo si la operación se confirmó |
| Docker / VPS de la cátedra | Despliegue del TP caps 1-4 | `docker build`/`docker run`, `--env-file`, sin Compose | Parcial (aparte) |

## API REST

### TP caps 1-4 (implementado)
Listados con `limit`/`offset`. `GET /health/ready` siempre 200 (el estado de la base va en el cuerpo).

| Recurso | Endpoints |
|---|---|
| health | `GET /health/live`, `GET /health/ready` |
| editoriales | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `GET /{id}/libros` |
| generos | `POST /`, `GET /`, `GET /{id}/libros` |
| autores | `POST /`, `GET /{id}`, `PATCH /{id}`, `GET /{id}/libros` |
| libros | `POST /` (con `autores`), `GET /` (`limit`, `offset`, `titulo`, `genero_id`), `GET /{id}`, `PATCH /{id}` (incl. stock) |
| clientes | `POST /`, `GET /{id}` (con perfil), `PATCH /{id}`, `POST /{id}/perfil`, `GET /{id}/ventas` |
| ventas | `POST /` (con `renglones`), `GET /`, `GET /{id}` |

Códigos por endpoint del TP:

| Endpoint | Códigos |
|---|---|
| `GET /health/live` | 200 |
| `GET /health/ready` | 200 (siempre; si la base no responde, `{"estado":"no listo","base":"sin conexión"}`) |
| `POST /editoriales/` | 201, 409, 422 |
| `GET /editoriales/` | 200, 422 |
| `GET /editoriales/{id}` | 200, 404, 422 |
| `PATCH /editoriales/{id}` | 200, 404, 409 |
| `GET /editoriales/{id}/libros` | 200, 404 |
| `POST /generos/` | 201, 409 |
| `GET /generos/` | 200 |
| `GET /generos/{id}/libros` | 200, 404 |
| `POST /autores/` | 201, 422 |
| `GET /autores/{id}` | 200, 404, 422 |
| `PATCH /autores/{id}` | 200, 404, 422 |
| `GET /autores/{id}/libros` | 200, 404 |
| `POST /libros/` | 201, 409, 422 |
| `GET /libros/` | 200, 422 |
| `GET /libros/{id}` | 200, 404 |
| `PATCH /libros/{id}` | 200, 404, 409, 422 |
| `POST /clientes/` | 201, 409, 422 |
| `GET /clientes/{id}` | 200, 404 |
| `PATCH /clientes/{id}` | 200, 404, 409, 422 |
| `POST /clientes/{id}/perfil` | 201, 404, 409 |
| `GET /clientes/{id}/ventas` | 200, 404 |
| `POST /ventas/` | 201, 409, 422 |
| `GET /ventas/` | 200, 422 |
| `GET /ventas/{id}` | 200, 404 (inferido) |

### Parcial caps 1-6 (pendiente)
La tabla de endpoints con grupo, método, rol y códigos está en `03_actores_y_roles.md` (es también la matriz de permisos). Cambios respecto del TP:

- Listados (`/libros`, `/editoriales`, `/generos`, `/ventas`, `/mis-ventas`, `/eventos`): `page` (desde 1), `size` (1–100, def. 20) y respuesta `{items, total, page, size, pages}`. Página más allá de la última → 422 ("La página 4 no existe: hay 3"). Con 0 resultados hay 1 página vacía. `total` cuenta con los mismos filtros que la página.
- `GET /health/ready` pasa a responder **503** si la base no contesta.
- Nuevos: `/auth/*`, `/usuarios*`, `/eventos`, `/mis-ventas`, `POST /libros/{id}/reponer`, `GET /libros/{id}/movimientos`, `DELETE /libros/{id}`.
- `POST /libros` recibe `stock_inicial` en lugar de `stock`; `PATCH /libros/{id}` no acepta `stock` (422 por `extra="forbid"`).
- Códigos: 201 al crear, 204 al dar de baja un libro, 404 si el recurso de la ruta no existe, 409 si choca con lo guardado, 422 si el cuerpo/parámetros no cumplen el contrato.

Ejemplos de cuerpo: `POST /ventas` (igual al TP) `{"cliente_id":2,"renglones":[{"libro_id":1,"cantidad":2},{"libro_id":4,"cantidad":1}]}` (no viajan precio, total ni fecha). `POST /libros`: `{"isbn":"978-950-00-0006-6","titulo":"Los que aman, odian","precio":"21000.00","stock_inicial":4,"editorial_id":1,"genero_id":1,"autores":[{"autor_id":3,"rol":"coautor","orden":1},{"autor_id":4,"rol":"coautor","orden":2}]}`. Login: `{"mensaje":"Sesión iniciada","debe_cambiar_password":false,"expira_en_segundos":1800}` (el token va solo en `Set-Cookie`).

> Verificación: el listado del TP se verificó contra el PDF del TP (SU-04); el del Parcial viene de una tabla entrelazada y se reconstruyó (ver `10_preguntas_abiertas.md`, IN-03).
