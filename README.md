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

## Pruebas automatizadas

1. Instalar las dependencias de desarrollo: `pip install -r requirements-dev.txt`.
2. Definir `TEST_DATABASE_URL` apuntando a una base PostgreSQL 16 **dedicada a tests** (si no se define, se usa `DATABASE_URL`). Debe usar el driver `postgresql+asyncpg`, por ejemplo:
   ```
   set TEST_DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/libreria_test
   ```
3. Ejecutar `pytest`. El esquema se crea automáticamente con `alembic upgrade head` y las tablas de dominio se limpian entre tests; nunca se usa `create_all`.

## Pendiente

- `alembic upgrade head` para crear el esquema (change C-03).
- Datos iniciales con `scripts/seed.py` (change C-03).
