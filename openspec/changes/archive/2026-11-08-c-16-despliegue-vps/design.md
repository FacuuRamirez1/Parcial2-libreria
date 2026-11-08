# Design

## Context

Estado actual (ver `proposal.md` - Why):
- `despliegue/` ya contiene el snapshot del TP caps 1-4 (tag `f1b9b48-snapshot-tp-cap1a4`) con `Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md` (sección C-15), `migrations/` (0001, 0002), `scripts/seed.py` y `test/`.
- `DEPLOY.md` tiene la sección C-15 (build, run, healthcheck, seed, actualización, seguridad) pero **falta la sección C-16** (URL pública, fecha/hora real, comandos completos con nombre de archivo de variables, cambios al TP, actualización).
- No existe `despliegue/evidencia/` (plantillas D-01..D-08).
- El entorno local **no tiene daemon de Docker** y el agente **no tiene acceso SSH ni credenciales** del VPS (IN-07 pendiente de la cátedra). Por tanto, todo `docker build`/`docker run`/captura de evidencia es acción manual del usuario en el VPS.
- `alembic upgrade head` arranca el contenedor; el seed usa `scripts/seed.py` del TP (IN-02b, IN-055).
- Dentro del contenedor la base NO está en `localhost`: `host.docker.internal` + `--add-host=host.docker.internal:host-gateway` (o la dirección que entregue la cátedra).
- `GET /health/ready` del TP responde 200 siempre (IN-09: no tocarlo en `despliegue/`).
- No se usa Docker Compose; no hay `.env` en la imagen; `DATABASE_URL` entra con `--env-file`.

## Goals / Non-Goals

**Goals:**
- Dejar `despliegue/DEPLOY.md` listo para ejecutar en el VPS con la sección C-16 completa (lugar para URL pública, fecha/hora, comandos `docker build`/`docker run` con nombre de archivo de variables sin su contenido, cambios al TP, procedimiento de actualización).
- Dejar `despliegue/evidencia/` con plantillas de encabezado de D-01..D-08 para que el usuario pegue la captura real.
- Documentar claramente las acciones manuales del usuario (SSH, credenciales, puerto, host de base, comandos exactos).
- No romper nada del TP ni del parcial: `openspec validate --all` sigue pasando y `python -m pytest -q` en verde.

**Non-Goals:**
- Ejecutar `docker build`/`docker run` (Docker no disponible localmente; despliegue real en VPS por el usuario).
- Capturar evidencia real del VPS (sin SSH ni credenciales).
- Modificar `app/`, `migrations/`, `scripts/seed.py`, `test/` del TP ni el código del parcial.
- Crear cambios fuera de C-16.

## Decisions

### D1. Estructura de `specs/` del change
3 capacidades en `openspec/changes/c-16-despliegue-vps/specs/<cap>/spec.md`:
- `despliegue-vps` (D-01, D-02, D-03, D-04)
- `despliegue-seguridad-contenedor` (D-05, D-06, D-07)
- `despliegue-auditoria-logs` (D-08)
Razón: cada una tiene un límite de comportamiento cohesivo y evita nombres catch-all. Alternativa (una spec por cada D) descartada por fragmentación excesiva sin beneficio de trazabilidad.

### D2. Comandos de despliegue en `DEPLOY.md` (C-16)
- Build: `docker build -t libreria .` (capa de deps antes del código, ya en el Dockerfile de C-15).
- Run: `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --add-host=host.docker.internal:host-gateway --env-file <archivo-variables> libreria`.
- Seed: `docker exec libreria python scripts/seed.py`.
- Salud: `docker ps` → `healthy`; `curl http://127.0.0.1:<puerto>/health/ready`.
- Actualización: `docker build -t libreria .` → `docker rm -f libreria` → mismo `docker run`.
Razón: reproduce los pasos de C-15 añadiendo `--add-host` (base remota) y el nombre del archivo de variables como marcador sin contenido (secreto).

### D3. Plantillas de evidencia
Archivos `despliegue/evidencia/D-01-build.txt` … `D-08-logs.txt` con:
- Encabezado: caso, qué verifica, comando/acción, fecha/hora (placeholder).
- Cuerpo: bloque de texto vacío/comentado `# <-- PEGAR AQUÍ LA SALIDA REAL DEL VPS`.
Razón: el usuario solo pega la salida real; el agente no puede generarla.

### D4. No se modifica el TP
Ni el Dockerfile, ni `.dockerignore`, ni `env.example` de C-15 (ya correctos). Solo se añade sección a `DEPLOY.md` y la carpeta `evidencia/`. Si al desplegar el contenedor no arranca, el defecto del TP se corrige y se anota en `DEPLOY.md` §5 (regla de C-15).

## Risks / Trade-offs

- [URL pública, puerto y host de base desconocidos (IN-07)] → El usuario los debe obtener de la cátedra y rellenar los placeholders de `DEPLOY.md` y `evidencia/`. Mitigación: placeholders explícitos y comandos exactos ya escritos.
- [Sin Docker local para validar] → No se puede confirmar que `docker build`/`docker run` funcionen. Mitigación: el Dockerfile y comandos copian los de C-15 (ya revisados); se deja nota de verificar en el VPS.
- [Base inaccesible → contenedor termina (D-05)] → Es comportamiento esperado por consigna; el HEALTHCHECK no salvará un contenedor que no arranca por falta de DB. Mitigación: documentar que `docker ps` mostrará `exited` si falta `DATABASE_URL`.
- [Healthcheck puede mostrar `healthy` aunque la base caiga después (IN-09)] → No se toca en `despliegue/` (regla del TP: 200 siempre). Mitigación: anotar en notas.

## Migration Plan

No aplica migración de datos (snapshot del TP caps 1-4, sin cambios de esquema). El despliegue es: build → run con variables → seed → verificar. Rollback: `docker rm -f libreria` y correr la versión anterior si se guardó la imagen previa.

## Open Questions

- ¿Puerto asignado, URL pública, host de la base y acceso SSH al VPS? (IN-07, decisor: cátedra) — pendiente; no bloquea los artefactos preparados.
- ¿Nombre exacto del archivo de variables de entorno en el VPS? → placeholder `<archivo-variables>` en `DEPLOY.md`; el usuario lo reemplaza por su `.env` real.
