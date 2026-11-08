# Proposal

## Why

El parcial caps 1-6 exige un cambio dedicado al despliegue del TP (Ejercicio 9, 11 pts, US-123, Flujo P12): empaquetar el snapshot del TP caps 1-4 en una imagen Docker reproducible, sin secretos en la imagen, con healthcheck y despliegue mediante `docker run --env-file`. Es independiente del código del parcial y puede ejecutarse desde ya, sobre el snapshot git `f1b9b48` ("Tests y detalles finales corregidos"), sin tocar C-01..C-07 ni el parcial.

## What Changes

- Crear tag de git sobre `f1b9b48` (snapshot del TP caps 1-4).
- Copiar ese estado a `despliegue/` (sin `.venv`, `__pycache__`, `.env`).
- Agregar solo en `despliegue/`:
  - `Dockerfile`: `python:3.12-alpine`, `requirements.txt` instalado antes del código con `pip install --no-cache-dir`, usuario no root, sin secretos, arranque con `alembic upgrade head` + `uvicorn app.main:app --host 0.0.0.0`, `HEALTHCHECK` a `127.0.0.1:8000/health/ready`.
  - `.dockerignore`: excluye `.env`, `.venv`, `.git`, `__pycache__`.
  - `env.example`: `DATABASE_URL` (sin valores) y `SQL_ECHO`.
  - `DEPLOY.md`: procedimiento, comandos exactos, cambios al TP, URL pública, fecha/hora, actualización.
- No Docker Compose. Evidencia de build y healthcheck `healthy`.
- No se modifica el código del TP ni el parcial.

## Capabilities

### New Capabilities
- `imagen-docker-tp-cap1a4`: Imagen Docker del TP caps 1-4 (build, arranque con migraciones + uvicorn, HEALTHCHECK en `/health/ready`, ejecución sin secretos vía `--env-file`, usuario no root). Es la capacidad de despliegue contenedor del TP.

### Modified Capabilities
- (ninguna: C-15 no altera el comportamiento de runtime de la API)

## Impact

- Nuevo directorio `despliegue/` con la copia del snapshot del TP y los archivos de contenedor.
- No afecta `app/`, `migrations/`, `test/`, `openspec/changes/c-01..c-14` ni el código del parcial.
- `DEPLOY.md` documenta la diferencia de variables de entorno entre el TP (`DATABASE_URL`) y el parcial (`POSTGRES_*`) (IN-07).
