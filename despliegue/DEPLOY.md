# Despliegue del TP caps 1-4 en contenedor (Change C-15)

> Documenta el procedimiento de despliegue de la imagen Docker del TP (caps 1-4).
> C-15 es independiente del parcial: trabaja sobre el snapshot git `f1b9b48`
> copiado a `despliegue/` y no modifica C-01..C-07 ni el código del parcial.

## 1. Resumen

- Imagen: `libreria` (base `python:3.12-alpine`).
- Origen: tag `f1b9b48-snapshot-tp-cap1a4` sobre el commit `f1b9b48` ("Tests y detalles finales corregidos").
- Directorio de trabajo: `despliegue/`.
- Arranque del contenedor: `alembic upgrade head` y luego `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- Healthcheck: `http://127.0.0.1:8000/health/ready` (wget de Alpine; `127.0.0.1` en vez de `localhost` porque `localhost` resuelve a `::1`).
- Variables de entorno: se pasan con `--env-file` (nunca en la imagen). `DATABASE_URL` y `SQL_ECHO`.
- Usuario: no root (`libreria`, uid 1000).
- Sin Docker Compose.

## 2. Fecha y hora del despliegue (preparación C-15)

- Fecha/hora de generación de los archivos: 2026-11-08 22:30 (hora local del entorno de desarrollo).
- URL pública: pendiente de definir en C-16 (despliegue en el VPS; requiere acceso al VPS de la cátedra).

## 3. Requisitos previos

- Docker 20.10+ instalado y daemon en ejecución.
- PostgreSQL 16 accesible (base de la cátedra en el VPS, o local en :5432 para pruebas).
- Un archivo de variables de entorno (copia de `despliegue/env.example` a `.env` o similar) con `DATABASE_URL` y `SQL_ECHO`. **No versionar `.env`.**

## 4. Comandos de despliegue (exactos)

Desde la carpeta `despliegue/`:

### 4.1 Construir la imagen

```sh
docker build -t libreria .
```

### 4.2 Ejecutar el contenedor

```sh
docker run -d --name libreria \
  -p 8000:8000 \
  --restart unless-stopped \
  --env-file .env \
  libreria
```

> Desde el contenedor la base de datos **no** está en `localhost`. Si la base corre en el host, usar `host.docker.internal` con `--add-host=host.docker.internal:host-gateway` y apuntar `DATABASE_URL` a ese host (o la dirección que entregue la cátedra).

### 4.3 Verificar healthcheck

```sh
docker ps
```

El contenedor debe aparecer con estado `healthy` (HEALTHCHECK sobre `127.0.0.1:8000/health/ready`).

### 4.4 Cargar datos iniciales (script del TP)

```sh
docker exec libreria python scripts/seed.py
```

### 4.5 Detener y eliminar

```sh
docker rm -f libreria
```

## 5. Cambios hechos al TP

- Se agregaron solo: `Dockerfile`, `.dockerignore`, `env.example` (ya presente en el snapshot) y `DEPLOY.md`.
- No se modificó el código de la aplicación, los modelos, las migraciones ni los tests del TP.
- No se aplicó ningún fix al TP: no se pudo ejecutar el contenedor en este entorno (daemon de Docker no disponible), por lo que no se verificó que arranque. Si al hacer `docker build`/`docker run` en el VPS el contenedor no levanta, corregir el defecto del TP y anotarlo aquí.

## 6. Procedimiento de actualización

1. Reconstruir la imagen: `docker build -t libreria .`
2. Detener y eliminar el contenedor anterior: `docker rm -f libreria`
3. Volver a ejecutar: `docker run -d --name libreria -p 8000:8000 --restart unless-stopped --env-file .env libreria`
4. Verificar `docker ps` → `healthy`.

Los datos viven en la base del servidor (fuera del contenedor), por lo que persisten entre actualizaciones; las migraciones no se duplican (`alembic_version` controla cuáles se aplican).

## 7. Notas de seguridad

- No hay secretos en la imagen ni en capas intermedias (`DATABASE_URL` entra por `--env-file`).
- El contenedor corre como usuario no root (`libreria`).
- Solo se publica el puerto de la aplicación (`8000`).
- `.env`, `.venv`, `.git` y `__pycache__` quedan excluidos de la imagen (`.dockerignore`).

## 8. Despliegue en el VPS (Change C-16)

> Esta sección se completa en el servidor de la cátedra (VPS). Requiere acceso SSH, credenciales, el puerto asignado y el host de la base de datos (pendiente de la cátedra, ver IN-07). El agente no tiene acceso SSH ni credenciales, por lo que todo `docker build`/`docker run`/captura de evidencia es acción manual del usuario.

### 8.1 URL pública y fecha/hora del despliegue

- URL pública del servicio: `http://<host-del-vps>:<puerto>/` (pendiente de definir por la cátedra; reemplazar `<host-del-vps>` y `<puerto>`).
- Fecha/hora del despliegue: pendiente de registrar al ejecutar los comandos de esta sección.

### 8.2 Archivo de variables de entorno

Copiar `despliegue/env.example` a un archivo de variables real (por ejemplo `despliegue/.env.vps` o similar, **no versionarlo**) y ajustar:

```dotenv
DATABASE_URL=postgresql+asyncpg://usuario:clave@<host-de-base>:5432/libreria
SQL_ECHO=false
```

- `<host-de-base>`: desde el contenedor la base NO está en `localhost`. Usar `host.docker.internal` con `--add-host=host.docker.internal:host-gateway`, o la dirección que entregue la cátedra.
- `DATABASE_URL` es obligatoria y sensible: entra con `--env-file`, nunca en la imagen ni en el repo.

### 8.3 Comandos de despliegue (exactos)

Desde la carpeta `despliegue/` del VPS:

#### 8.3.1 Construir la imagen

```sh
docker build -t libreria .
```

#### 8.3.2 Ejecutar el contenedor

```sh
docker run -d --name libreria \
  -p <puerto>:8000 \
  --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  --env-file <archivo-de-variables> \
  libreria
```

Reemplazar `<puerto>` por el puerto asignado y `<archivo-de-variables>` por el nombre del archivo creado en 8.2 (por ejemplo `.env.vps`). Al arrancar, el contenedor ejecuta `alembic upgrade head` y luego uvicorn en `0.0.0.0:8000`.

> Si falta `DATABASE_URL` o la base es inaccesible, el contenedor termina con error (caso D-05): no queda sirviendo.

#### 8.3.3 Verificar healthcheck

```sh
docker ps
```

El contenedor debe aparecer con estado `healthy` (HEALTHCHECK sobre `127.0.0.1:8000/health/ready`).

Desde afuera del contenedor:

```sh
curl http://127.0.0.1:<puerto>/health/ready
```

Debe responder `200`.

#### 8.3.4 Cargar datos iniciales (script del TP)

```sh
docker exec libreria python scripts/seed.py
```

Desde afuera, verificar la API:

```sh
curl -i http://127.0.0.1:<puerto>/libros/
curl -i -X POST http://127.0.0.1:<puerto>/ventas/ -H "Content-Type: application/json" -d '{"cliente_id":1,"renglones":[{"libro_id":1,"cantidad":1}]}'
```

Esperados: `GET /libros/` → `200`; `POST /ventas/` → `201`. El aviso de comprobante aparece en `docker logs libreria` tras la respuesta (caso D-08).

#### 8.3.5 Actualización del servicio (sin perder datos ni repetir migraciones)

```sh
docker build -t libreria .
docker rm -f libreria
docker run -d --name libreria \
  -p <puerto>:8000 \
  --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  --env-file <archivo-de-variables> \
  libreria
```

Los datos viven en la base del servidor (fuera del contenedor), por lo que persisten entre actualizaciones; las migraciones no se duplican (`alembic_version` controla cuáles se aplican).

### 8.4 Cambios hechos al TP

- Se agregaron solo: `Dockerfile`, `.dockerignore`, `env.example` y `DEPLOY.md` (estas dos últimas ya presentes en el snapshot de C-15; C-16 añade la sección 8 de `DEPLOY.md` y la carpeta `evidencia/`).
- No se modificó el código de la aplicación, los modelos, las migraciones ni los tests del TP.
- No se aplicó ningún fix al TP: no se pudo ejecutar el contenedor en este entorno de desarrollo (daemon de Docker no disponible). Si al hacer `docker build`/`docker run` en el VPS el contenedor no levanta, corregir el defecto del TP y anotarlo aquí.

### 8.5 Evidencia (casos D-01..D-08)

Cada caso tiene una plantilla en `despliegue/evidencia/`:

| Caso | Qué verifica | Archivo |
|------|-------------|---------|
| D-01 | Imagen construida en `despliegue/` | `D-01-build.txt` |
| D-02 | Healthcheck `healthy` | `D-02-healthcheck.txt` |
| D-03 | Datos cargados + API responde | `D-03-datos-api.txt` |
| D-04 | Actualización sin perder datos ni repetir migraciones | `D-04-actualizacion.txt` |
| D-05 | Base inaccesible → contenedor termina | `D-05-base-inaccesible.txt` |
| D-06 | Sin secretos en la imagen | `D-06-sin-secretos.txt` |
| D-07 | Usuario no root | `D-07-no-root.txt` |
| D-08 | Aviso de comprobante en logs | `D-08-logs.txt` |

El usuario pega la salida real del VPS en cada archivo (bajo el encabezado de cada plantilla).

### 8.6 Acciones manuales del usuario (resumen)

1. Obtener de la cátedra: acceso SSH al VPS, credenciales, puerto asignado, host de la base y URL pública (IN-07 pendiente).
2. Conectar por SSH al VPS y clonar/copiar este repositorio (o al menos `despliegue/`).
3. Crear el archivo de variables de entorno (copia de `env.example`) con `DATABASE_URL` y `SQL_ECHO=false`; **no versionarlo**.
4. Ejecutar los comandos de 8.3 en orden: build → run → verificar healthcheck → seed → verificar API.
5. Capturar la salida de cada caso D en `despliegue/evidencia/D-XX-*.txt`.
6. Para actualizar: repetir 8.3.5.

