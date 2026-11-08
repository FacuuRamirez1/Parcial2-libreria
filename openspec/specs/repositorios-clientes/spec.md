# repositorios-clientes Specification

## Purpose

Define el contrato del repositorio de la entidad Cliente: obtención por id, listado paginado, búsqueda por email, conteo y escritura mediante flush, sin carga perezosa.

## Requirements

### Requirement: Obtención de cliente por id

El repositorio SHALL devolver el cliente solicitado por su id o nulo si no existe.

#### Scenario: Cliente existente

- **WHEN** se consulta el repositorio por un id de cliente presente
- **THEN** devuelve la entidad Cliente correspondiente

#### Scenario: Cliente inexistente

- **WHEN** se consulta el repositorio por un id de cliente ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Búsqueda de cliente por email

El repositorio SHALL devolver el cliente que coincide con un email o nulo si no existe.

#### Scenario: Cliente por email existente

- **WHEN** se consulta por un email registrado
- **THEN** devuelve la entidad Cliente con ese email

#### Scenario: Cliente por email inexistente

- **WHEN** se consulta por un email no registrado
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Listado paginado de clientes

El repositorio SHALL listar clientes aplicando `offset`/`limit` y orden estable por id.

#### Scenario: Listado con paginación

- **WHEN** se solicita `get_all` con `offset` y `limit`
- **THEN** devuelve hasta `limit` clientes empezando en `offset`, ordenados por id

### Requirement: Conteo de clientes

El repositorio SHALL devolver la cantidad total de clientes.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla cliente

### Requirement: Escritura de cliente mediante flush

El repositorio SHALL agregar, actualizar o eliminar un cliente con `flush()` y nunca con `commit()`.

#### Scenario: Alta de cliente

- **WHEN** se invoca `add` con una entidad Cliente y se hace flush
- **THEN** el cliente persiste en la transacción abierta sin confirmarla
