# Design

## Context

El cambio trabaja sobre una copia del snapshot git `f1b9b48` (TP caps 1-4), no sobre el código actual del parcial. Ese TP usa `DATABASE_URL` + `python-dotenv` (no `POSTGRES_*` ni `Settings`), tiene migraciones 0001 y 0002, script `scripts/seed.py`, y arranca con `uvicorn app.main:app`. El Dockerfile y el punto de entrada deben casar con esa estructura. El daemon de Docker no está disponible en este entorno, por lo que el build y el healthcheck no se pudieron ejecutar aquí; los archivos quedan listos para C-16.

## Goals / Non-Goals

**Goals:**
- Imagen reproducible en `despliegue/` sobre `python:3.12-alpine` (< 100 MB ideal).
- Capa de dependencias instalada antes del código (`requirements.txt` + `--no-cache-dir`) para caché de Docker.
- Usuario no root (`USER`); sin secretos en la imagen ni en capas intermedias.
- Arranque: `alembic upgrade head` y luego `uvicorn app.main:app --host 0.0.0.0`.
- `HEALTHCHECK` sobre `127.0.0.1:8000/health/ready` (Alpine trae `wget`; `localhost` resuelve a `::1`).
- `env.example` con `DATABASE_URL` (sin valores) y `SQL_ECHO`; `.dockerignore` que excluya `.env`, `.venv`, `.git`, `__pycache__`.
- `DEPLOY.md` con comandos exactos, cambios al TP, URL pública, fecha/hora y procedimiento de actualización.

**Non-Goals:**
- No Docker Compose.
- No modificar C-01..C-07 ni el parcial.
- No corregir defectos del TP salvo que impidan el arranque en contenedor (y anotarlo en DEPLOY.md).

## Decisions

### 1. Tag de git sobre f1b9b48 y copia a despliegue/
Se crea `git tag f1b9b48-snapshot-tp-cap1a4 f1b9b48` y se copia el árbol de ese commit a `despliegue/` excluyendo `.venv`, `__pycache__`, `.env`. Razón: C-15 debe ser un snapshot inmutable del TP caps 1-4 (DD-13), independiente del parcial.
- Alternativa considerada: copiar el árbol de trabajo actual. Rechazada: incluiría cambios del parcial (usuarios, auth, repositorios, UoW), violando el alcance de C-15.

### 2. Dockerfile: capas y orden
`FROM python:3.12-alpine` → `WORKDIR /app` → copiar e instalar `requirements.txt` (`pip install --no-cache-dir`) → copiar el código → crear usuario no root → `USER` → `HEALTHCHECK` → `CMD` sh -c "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000".
Razón: instalar dependencias antes del código aprovecha el caché de capas. El punto de entrada combina migraciones + uvicorn en un solo comando para que `alembic upgrade head` se ejecute antes de levantar la API.
Alternativa considerada: entrypoint script separado. Rechazada: agrega un archivo más; el sh -c cumple el requisito sin complejidad extra.

### 3. Variables de entorno
`env.example` declara `DATABASE_URL` (sin valor) y `SQL_ECHO=false`. En tiempo de ejecución se provee con `--env-file` al `docker run`; nunca en el Dockerfile ni en la imagen. Desde el contenedor la base no está en `localhost` (usa `host.docker.internal` + `--add-host=host.docker.internal:host-gateway`, anotado en DEPLOY.md).

### 4. HEALTHCHECK
`HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 CMD wget --quiet --tries=1 --spider http://127.0.0.1:8000/health/ready || exit 1`.
Razón: Alpine trae `wget` (no `curl`); `127.0.0.1` evita la resolución IPv6 de `localhost` a `::1`.

### 5. No create_all ni cambios al esquema
El TP usa solo Alembic (0001, 0002). El contenedor corre `alembic upgrade head`; no se agrega `create_all`.

## Risks / Trade-offs

[El daemon de Docker no está disponible en este entorno] → Se documenta que el build y el healthcheck no se pudieron ejecutar aquí; los archivos de `despliegue/` están listos para C-16, donde sí habrá Docker.
[health/ready del TP responde 200 siempre (IN-09)] → El contenedor puede figurar `healthy` aunque la base esté caída. No se toca en `despliegue/` (respeta la consigna del TP); se anota en DEPLOY.md.
[DATABASE_URL vs POSTGRES_*] → `despliegue/` usa `DATABASE_URL` (TP); el parcial usa `POSTGRES_*`. Se documenta la diferencia en DEPLOY.md para evitar mezclar archivos.

## Migration Plan

1. `git tag f1b9b48-snapshot-tp-cap1a4 f1b9b48`
2. Copiar árbol de f1b9b48 a `despliegue/` (sin `.venv`, `__pycache__`, `.env`).
3. Crear `despliegue/Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md`.
4. (C-16) `docker build -t libreria .` en `despliegue/`; `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> libreria`; verificar `docker ps` → `healthy`.

## Open Questions

- Puerto asignado, URL pública, host de la base y acceso SSH al VPS: definidos por la cátedra en C-16 (no bloquean C-15).
- ¿Nombre exacto del tag?: se usa `f1b9b48-snapshot-tp-cap1a4` (suficiente; ajustable en C-16).
