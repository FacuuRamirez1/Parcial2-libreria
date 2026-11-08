# Spec Delta

## Purpose

Define el contrato de lectura y escritura del repositorio de la entidad Autor: obtención por id, listado paginado, conteo y creación/actualización/eliminación mediante flush, sin carga perezosa.

## ADDED Requirements

### Requirement: Obtención de autor por id

El repositorio SHALL devolver el autor solicitado por su identificador o nulo si no existe.

#### Scenario: Autor existente

- **WHEN** se consulta el repositorio por un id de autor presente en la base
- **THEN** devuelve la entidad Autor correspondiente

#### Scenario: Autor inexistente

- **WHEN** se consulta el repositorio por un id de autor ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Listado paginado de autores

El repositorio SHALL listar autores aplicando `offset`/`limit` y orden estable por id.

#### Scenario: Listado con paginación

- **WHEN** se solicita `get_all` con `offset` y `limit`
- **THEN** devuelve hasta `limit` autores empezando en `offset`, ordenados por id

### Requirement: Conteo de autores

El repositorio SHALL devolver la cantidad total de autores.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla autor

### Requirement: Escritura de autor mediante flush

El repositorio SHALL agregar, actualizar o eliminar un autor con `flush()` y nunca con `commit()`.

#### Scenario: Alta de autor

- **WHEN** se invoca `add` con una entidad Autor y se hace flush
- **THEN** el autor persiste en la transacción abierta sin confirmarla
