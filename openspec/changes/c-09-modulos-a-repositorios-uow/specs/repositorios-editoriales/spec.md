# Spec Delta

## Purpose

Define el contrato de lectura y escritura del repositorio de la entidad Editorial: obtención por id, listado paginado, conteo y creación/actualización/eliminación mediante flush, sin carga perezosa.

## ADDED Requirements

### Requirement: Obtención de editorial por id

El repositorio SHALL devolver la editorial solicitada por su identificador o nulo si no existe.

#### Scenario: Editorial existente

- **WHEN** se consulta el repositorio por un id de editorial presente en la base
- **THEN** devuelve la entidad Editorial correspondiente

#### Scenario: Editorial inexistente

- **WHEN** se consulta el repositorio por un id de editorial ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Listado paginado de editoriales

El repositorio SHALL listar editoriales aplicando `offset`/`limit` y orden estable por id.

#### Scenario: Listado con paginación

- **WHEN** se solicita `get_all` con `offset` y `limit`
- **THEN** devuelve hasta `limit` editoriales empezando en `offset`, ordenadas por id

### Requirement: Conteo de editoriales

El repositorio SHALL devolver la cantidad total de editoriales.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla editorial

### Requirement: Escritura de editorial mediante flush

El repositorio SHALL agregar, actualizar o eliminar una editorial con `flush()` y nunca con `commit()`.

#### Scenario: Alta de editorial

- **WHEN** se invoca `add` con una entidad Editorial y se hace flush
- **THEN** la editorial persiste en la transacción abierta sin confirmarla

#### Scenario: Actualización de editorial

- **WHEN** se modifica un atributo de una Editorial recuperada y se hace flush
- **THEN** el cambio se refleja en la transacción abierta sin confirmarla
