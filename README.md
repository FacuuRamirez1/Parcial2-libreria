# Librería - API (Parcial 2)

API en FastAPI + SQLModel + PostgreSQL (asincrónica).

## Puesta en marcha

1. Crear y activar un entorno virtual con Python 3.12:
   ```
   py -3.12 -m venv .venv
   .venv\Scripts\activate
   ```
2. Instalar dependencias: `pip install -r requirements.txt`
3. Copiar `env.example` a `.env` y ajustar usuario y clave de tu PostgreSQL local (el `.env` no se versiona).
4. Crear la base `libreria` en tu PostgreSQL 16 local (por ejemplo `createdb libreria`).
5. Arrancar: `uvicorn app.main:app --reload` (o `fastapi dev`).
6. Probar con `test/health.http` (extensión REST Client de VS Code o similar): `/health/live` y `/health/ready`.

Variables de entorno: `DATABASE_URL` (obligatoria, driver `postgresql+asyncpg`) y `SQL_ECHO` (`true` muestra el SQL en consola).

## Pendiente

- `alembic upgrade head` para crear el esquema (change C-03).
- Datos iniciales con `scripts/seed.py` (change C-03).
