# Spec Delta

## Purpose

Define el contrato de lectura y escritura del repositorio de la entidad Género: obtención por id, listado paginado, conteo y creación/actualización/eliminación mediante flush, sin carga perezosa.

## ADDED Requirements

### Requirement: Obtención de género por id

El repositorio SHALL devolver el género solicitado por su identificador o nulo si no existe.

#### Scenario: Género existente

- **WHEN** se consulta el repositorio por un id de género presente en la base
- **THEN** devuelve la entidad Genero correspondiente

#### Scenario: Género inexistente

- **WHEN** se consulta el repositorio por un id de género ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Listado paginado de géneros

El repositorio SHALL listar géneros aplicando `offset`/`limit` y orden estable por id.

#### Scenario: Listado con paginación

- **WHEN** se solicita `get_all` con `offset` y `limit`
- **THEN** devuelve hasta `limit` géneros empezando en `offset`, ordenados por id

### Requirement: Conteo de géneros

El repositorio SHALL devolver la cantidad total de géneros.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla genero

### Requirement: Escritura de género mediante flush

El repositorio SHALL agregar, actualizar o eliminar un género con `flush()` y nunca con `commit()`.

#### Scenario: Alta de género

- **WHEN** se invoca `add` con una entidad Genero y se hace flush
- **THEN** el género persiste en la transacción abierta sin confirmarla
