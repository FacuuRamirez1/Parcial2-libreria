# despliegue-seguridad-contenedor Specification

## Purpose
Definir las garantías de seguridad del contenedor del TP desplegado: sin secretos embebidos, contenedor que termina si la base es inaccesible y ejecución como usuario no root.

## Requirements

### Requirement: Base inaccesible -> contenedor termina
Sin `DATABASE_URL` o con la base inaccesible, el contenedor SHALL terminar con error y no quedar sirviendo.

#### Scenario: D-05 base inaccesible
- **WHEN** se ejecuta `docker run` sin `DATABASE_URL` o con base inaccesible
- **THEN** el contenedor termina con error y no sirve peticiones

### Requirement: Sin secretos en la imagen
La imagen SHALL no contener `.env` y `docker run --rm --entrypoint env <imagen>` SHALL no mostrar `DATABASE_URL`.

#### Scenario: D-06 sin secretos
- **WHEN** se inspecciona la imagen con `docker run --rm --entrypoint ls -a /app` y `docker run --rm --entrypoint env <imagen>`
- **THEN** no hay `.env` en `/app` y `env` no muestra `DATABASE_URL`

### Requirement: Usuario no root
El contenedor SHALL ejecutarse como usuario no root (`id` != 0).

#### Scenario: D-07 no root
- **WHEN** se ejecuta `docker exec libreria id`
- **THEN** el resultado no es `uid=0(root)`
