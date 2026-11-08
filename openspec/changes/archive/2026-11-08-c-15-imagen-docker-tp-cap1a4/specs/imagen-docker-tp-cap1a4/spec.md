# Spec Delta

## Purpose

Define el comportamiento observable de la imagen Docker del TP caps 1-4: construcción reproducible, arranque con migraciones y uvicorn, HEALTHCHECK en /health/ready y ejecución sin secretos embebidos.

## ADDED Requirements

### Requirement: Imagen construible sobre python:3.12-alpine
La imagen SHALL construirse con `FROM python:3.12-alpine`, instalando `requirements.txt` con `pip install --no-cache-dir` antes de copiar el código, sin secretos en ninguna capa y ejecutando como usuario no root (`USER`).

#### Scenario: Build exitoso sin secretos
- **WHEN** se ejecuta `docker build` en `despliegue/`
- **THEN** la imagen se construye, `docker history` no muestra `DATABASE_URL` ni contraseñas, y el contenedor corre como usuario no root (`id` != 0)

### Requirement: Arranque con migraciones y uvicorn
Al iniciar el contenedor SHALL ejecutarse `alembic upgrade head` y, solo si exitoso, `uvicorn app.main:app --host 0.0.0.0`, escuchando en el puerto 8000.

#### Scenario: Arranque y puerto
- **WHEN** se ejecuta `docker run` con `--env-file` que provea `DATABASE_URL`
- **THEN** el contenedor aplica migraciones y responde en el puerto 8000; si falta `DATABASE_URL`, el contenedor termina con error

### Requirement: Healthcheck sobre 127.0.0.1
La imagen SHALL declarar un `HEALTHCHECK` que consulte `http://127.0.0.1:8000/health/ready` (no `localhost`, porque Alpine solo trae `wget` que resuelve a `::1`).

#### Scenario: Healthcheck healthy
- **WHEN** el contenedor está arriba y la base responde
- **THEN** `docker ps` reporta el estado `healthy`
