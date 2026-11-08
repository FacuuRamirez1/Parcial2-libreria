# Tasks

## 1. Snapshot del TP y copia a despliegue/

- [ ] 1.1 Crear tag de git `f1b9b48-snapshot-tp-cap1a4` sobre `f1b9b48` y verificar que existe (`git tag -l`) — verificación: `git rev-parse f1b9b48-snapshot-tp-cap1a4` devuelve `f1b9b48`.
- [ ] 1.2 Crear `despliegue/` y copiar el árbol de `f1b9b48` sin `.venv`, `__pycache__`, `.env` — verificación: `despliegue/` existe y no contiene `.env`, `__pycache__` ni `.venv`; contiene `app/`, `migrations/`, `scripts/seed.py`, `requirements.txt`, `alembic.ini`, `env.example`, `test/`.

## 2. Archivos de contenedor en despliegue/

- [ ] 2.1 Crear `despliegue/Dockerfile` (`python:3.12-alpine`, `requirements.txt` antes del código con `--no-cache-dir`, usuario no root, sin secretos, `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0`, `HEALTHCHECK` a `127.0.0.1:8000/health/ready`) — verificación: archivo presente y cumple cada requisito del spec.
- [ ] 2.2 Crear `despliegue/.dockerignore` que excluya `.env`, `.venv`, `.git`, `__pycache__` — verificación: archivo presente con las cuatro exclusiones.
- [ ] 2.3 Crear `despliegue/env.example` con `DATABASE_URL` (sin valor) y `SQL_ECHO` — verificación: archivo presente con ambas variables y sin valores reales.
- [ ] 2.4 Crear `despliegue/DEPLOY.md` con procedimiento, comandos `docker build` y `docker run` exactos, cambios al TP, URL pública, fecha/hora y procedimiento de actualización — verificación: archivo presente y completo.

## 3. Build de imagen y healthcheck (si Docker disponible)

- [ ] 3.1 Ejecutar `docker build -t libreria .` en `despliegue/` — verificación: build exitoso; imagen `libreria` listada en `docker images`.
- [ ] 3.2 Ejecutar `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> libreria` y verificar `docker ps` → `healthy` — verificación: contenedor en estado `healthy` (HEALTHCHECK sobre `127.0.0.1`).
- [ ] 3.3 Si Docker no está disponible (daemon sin correr), documentar en DEPLOY.md / resultado que el build y healthcheck no se pudieron ejecutar pero los archivos están listos — verificación: nota registrada en el resumen de apply.

## 4. Validación del proyecto

- [ ] 4.1 Ejecutar `python -m pytest -q` en la raíz del proyecto — verificación: cantidad de tests pasados / fallados reportada en el resumen final.

## Workflow follow-up

- Archive el change tras completar apply y validación (`openspec instructions archive --change "c-15-imagen-docker-tp-cap1a4" --json`).
