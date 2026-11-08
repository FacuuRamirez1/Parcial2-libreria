# Descripción General

## Stack tecnológico

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI (todos los handlers `async def`) | 0.111 |
| Modelos y contratos | SQLModel | 0.0.24 |
| ORM / motor / sesión | SQLAlchemy asincrónico | 2.0 |
| Driver | asyncpg | 0.30 |
| Base de datos | PostgreSQL | 16 |
| Migraciones | Alembic (plantilla asincrónica) | 1.13 |
| Configuración | python-dotenv | 1.0 |
| Servidor ASGI | uvicorn (el que instala `fastapi[standard]`) | — |

La dirección de la base se lee de la variable `DATABASE_URL`, definida en `.env` (no versionado). El repo incluye `env.example` sin secretos.

## Arquitectura general

API backend pura, organizada por módulo funcional. Cada módulo tiene la misma estructura: `models.py` (tablas), `schemas.py` (DTO), `service.py` (lógica) y `router.py` (HTTP). La lógica vive en el service, que recibe la sesión como parámetro.

```
Cliente HTTP
   │
   ▼
router.py  (valida, delega, declara respuesta/códigos)
   │  Depends(get_session): una sesión por petición
   ▼
service.py (lógica, traducción de IntegrityError, lecturas con precarga)
   │
   ▼
SQLModel / SQLAlchemy async ── asyncpg ──► PostgreSQL 16
```

Ciclo de vida: el motor asincrónico y la fábrica de sesiones se crean en el `lifespan`, se guardan en `app.state` y el motor se cierra al apagar. Las sesiones se crean con `expire_on_commit=False`.

## Integraciones externas

| Servicio | Propósito | Tipo |
|---|---|---|
| PostgreSQL 16 | Persistencia | Driver asyncpg |
| Aviso de comprobante (simulado) | Notificar al cliente tras una venta | `BackgroundTasks` + `await asyncio.sleep(0.5)` + log; sin servicio real |

## API REST

Referencia según la consigna. Los listados paginan con `limit` y `offset`.

| Recurso | Endpoints |
|---|---|
| health | `GET /health/live` (no toca la base), `GET /health/ready` (`SELECT 1`; siempre responde 200, el estado de la base va en el cuerpo) |
| editoriales | `POST /`, `GET /`, `GET /{id}`, `PATCH /{id}`, `GET /{id}/libros` |
| generos | `POST /`, `GET /`, `GET /{id}/libros` |
| autores | `POST /`, `GET /{id}`, `PATCH /{id}`, `GET /{id}/libros` (con rol y orden) |
| libros | `POST /` (con `autores`), `GET /` (`limit`, `offset`, `titulo`, `genero_id`), `GET /{id}`, `PATCH /{id}` |
| clientes | `POST /`, `GET /{id}` (con perfil), `PATCH /{id}`, `POST /{id}/perfil`, `GET /{id}/ventas` |
| ventas | `POST /` (con `renglones`), `GET /`, `GET /{id}` |

Códigos: 201 al crear, 200 en lecturas y PATCH, 404 si no existe, 409 si la base rechaza la escritura, 422 si el cuerpo o los parámetros no cumplen el contrato.

> El listado de endpoints y los códigos fueron verificados contra el PDF de la consigna (única corrección: se quitó `GET /autores/`, que no figura en el PDF). Ver SU-04 en `09_decisiones_y_supuestos.md`.

### Códigos por endpoint (según el PDF)

| Endpoint | Códigos |
|---|---|
| `GET /health/live` | 200 |
| `GET /health/ready` | 200 (siempre; si la base no responde, el cuerpo es `{"estado":"no listo","base":"sin conexión"}`) |
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
| `GET /ventas/{id}` | 200, 404 (inferido: el PDF cortó los códigos de esta fila) |
