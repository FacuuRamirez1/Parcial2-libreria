# despliegue-vps Specification

## Purpose
Definir el comportamiento observable del despliegue del TP caps 1-4 en el VPS: construcción de la imagen en el servidor, arranque con migraciones y uvicorn, acceso a la base remota (no localhost), carga de datos, healthcheck y actualización sin repetir migraciones.

## Requirements

### Requirement: Imagen construida en el servidor
La imagen `libreria` SHALL construirse con `docker build -t libreria .` dentro de `despliegue/` (snapshot del TP caps 1-4 sobre `f1b9b48`).

#### Scenario: D-01 build exitoso
- **WHEN** se ejecuta `docker build -t libreria .` en `despliegue/` del VPS
- **THEN** la imagen se construye sin errores y aparece en `docker images`

### Requirement: Healthcheck healthy
El contenedor SHALL declarar un `HEALTHCHECK` sobre `http://127.0.0.1:8000/health/ready` y reportar estado `healthy`.

#### Scenario: D-02 healthcheck
- **WHEN** el contenedor está arriba y la base responde
- **THEN** `docker ps` reporta el estado `healthy`

### Requirement: Datos cargados y API responde
Tras el arranque, SHALL cargarse el seed con `docker exec libreria python scripts/seed.py` y desde afuera SHALL responder `GET /health/ready` (200), `GET /libros/` (200) y `POST /ventas/` (201).

#### Scenario: D-03 datos y API
- **WHEN** se ejecuta `docker exec libreria python scripts/seed.py` y luego peticiones desde fuera del contenedor
- **THEN** `GET /health/ready` → 200, `GET /libros/` → 200 con ítems y `POST /ventas/` → 201
- **AND** `docker logs libreria` muestra el aviso de comprobante tras la respuesta (D-08)

### Requirement: Actualización sin perder datos ni repetir migraciones
Al recrear el contenedor con el mismo `docker run`, SHALL volver a `healthy`, los datos SHALL seguir presentes y las migraciones SHALL no repetirse (controladas por `alembic_version`).

#### Scenario: D-04 actualización
- **WHEN** se ejecuta `docker rm -f libreria` y el mismo `docker run` de nuevo
- **THEN** el contenedor vuelve a `healthy`, los datos persisten y `alembic upgrade head` no aplica migraciones ya aplicadas
