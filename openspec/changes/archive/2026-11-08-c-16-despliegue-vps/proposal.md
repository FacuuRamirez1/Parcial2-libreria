# Proposal

## Why

El TP caps 1-4 ya tiene su imagen Docker lista (C-15) sobre el snapshot `f1b9b48`, copiada en `despliegue/`, pero todavía no se desplegó en el VPS de la cátedra ni se validó contra los casos D-01..D-08 de US-124. C-16 cubre el despliegue real en el servidor: construir la imagen en el VPS, ejecutarla con la base de la cátedra (`DATABASE_URL` y `SQL_ECHO` por variable de entorno, nunca en la imagen; la base no está en `localhost` dentro del contenedor → `host.docker.internal` + `--add-host=host.docker.internal:host-gateway`), cargar los datos, verificar el healthcheck, actualizar sin repetir migraciones y dejar plantillas de evidencia para que el usuario capture la salida real. Depende de C-15 (imagen ya lista en `despliegue/`).

## What Changes

- Completar `despliegue/DEPLOY.md` con la sección C-16: lugar para URL pública, fecha/hora real del despliegue, comandos `docker build` y `docker run` completos (con el nombre del archivo de variables, SIN su contenido), cambios hechos al TP y cómo se actualiza (rebuild → `docker rm -f` → `docker run`).
- Crear `despliegue/evidencia/` con plantillas de D-01..D-08 (`D-01-build.txt` … `D-08-logs.txt`) con encabezado y espacio para la captura real del VPS.
- Escribir los artefactos OPSX del change: `proposal.md`, `specs/despliegue-vps/spec.md`, `specs/despliegue-seguridad-contenedor/spec.md`, `specs/despliegue-auditoria-logs/spec.md`, `design.md` y `tasks.md`.
- No tocar el código del parcial ni de C-01..C-07; solo `despliegue/` y la carpeta del change.
- Toda la ejecución real (`docker build`, `docker run`, captura de evidencia) queda como acción manual del usuario en el VPS (el agente no tiene SSH ni credenciales, y el entorno local no tiene daemon de Docker).

## Capabilities

### New Capabilities

- `despliegue-vps`: Despliegue del TP en el VPS: build de imagen en servidor, `docker run` con `DATABASE_URL`/`SQL_ECHO` por `--env-file`, base remota vía `host.docker.internal` + `--add-host`, healthcheck en `127.0.0.1:8000/health/ready`, carga de datos con `docker exec` y actualización sin repetir migraciones. Cubre D-01, D-02, D-03, D-04.
- `despliegue-seguridad-contenedor`: Garantías de seguridad del contenedor desplegado: sin `.env`/secretos en la imagen, `DATABASE_URL` ausente de `env`, base inaccesible → el contenedor termina sin servir, usuario no root. Cubre D-05, D-06, D-07.
- `despliegue-auditoria-logs`: El aviso de comprobante se registra en `docker logs libreria` tras la línea de respuesta HTTP. Cubre D-08.

### Modified Capabilities

(Ninguna: C-16 no cambia requisitos de capacidades existentes; solo añade el despliegue operativo sobre la imagen ya construida por C-15.)

## Impact

- `despliegue/DEPLOY.md` (sección C-16 nueva).
- `despliegue/evidencia/` (carpeta nueva con 8 plantillas de captura).
- `openspec/changes/c-16-despliegue-vps/` (proposal, specs, design, tasks).
- Ningún cambio a `app/`, `migrations/`, `test/`, `scripts/seed.py` del TP ni al código del parcial.
