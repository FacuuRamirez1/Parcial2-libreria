# Tasks

## 1. Verificar archivos de C-15 en `despliegue/`

- [x] 1.1 Verificar que `despliegue/` tiene `Dockerfile`, `.dockerignore`, `env.example` y `DEPLOY.md` (hecho en C-15; verificar contenido) — verificar: `ls despliegue/` muestra los 4 archivos
- [x] 1.2 Confirmar dependencia C-15 satisfecha (tag `f1b9b48-snapshot-tp-cap1a4` existe y snapshot copiado) — verificar: `git tag -l | grep f1b9b48` y `despliegue/Dockerfile` usa `python:3.12-alpine` + `USER libreria` + HEALTHCHECK `127.0.0.1`

## 2. Completar `despliegue/DEPLOY.md` con sección C-16

- [x] 2.1 Agregar sección C-16 a `DEPLOY.md`: lugar para URL pública, fecha/hora real, comandos `docker build` y `docker run` completos (nombre de archivo de variables, SIN su contenido), cambios hechos al TP y procedimiento de actualización — verificar: `DEPLOY.md` contiene sección "C-16" con comandos exactos
- [x] 2.2 Incluir nota de base remota (`host.docker.internal` + `--add-host=host.docker.internal:host-gateway`) y que `DATABASE_URL` entra con `--env-file` (nunca en la imagen) — verificar: sección C-16 menciona ambas

## 3. Crear `despliegue/evidencia/` con plantillas D-01..D-08

- [x] 3.1 Crear carpeta `despliegue/evidencia/` — verificar: carpeta existe
- [x] 3.2 Crear plantillas `D-01-build.txt` … `D-08-logs.txt` con encabezado y espacio para captura real — verificar: 8 archivos en `despliegue/evidencia/`

## 4. Documentar acciones manuales del usuario

- [x] 4.1 Listar en `DEPLOY.md` (o tasks) qué necesita el usuario: SSH al VPS, credenciales, puerto, host de base (IN-07 pendiente de cátedra) — verificar: sección de acciones manuales presente
- [x] 4.2 Dejar comandos exactos de build/run/seed/verificación listos para copiar-pegar en el VPS — verificar: comandos exactos en `DEPLOY.md`

## 5. Validar que nada se rompió

- [x] 5.1 Ejecutar `openspec validate --all` — verificar: 0 fallos, incluido `change/c-16-despliegue-vps`
- [x] 5.2 Ejecutar `python -m pytest -q` en la raíz del proyecto — verificar: tests en verde (39 passed)

## Workflow follow-up

- El usuario ejecuta el despliegue real en el VPS (comandos de `DEPLOY.md`) y captura la evidencia en `despliegue/evidencia/`.
- Una vez completado, ejecutar `openspec archive c-16-despliegue-vps` y marcar `[x]` en `CHANGES.md`.
