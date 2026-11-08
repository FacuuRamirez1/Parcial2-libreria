# repositorios-ventas Specification

## Purpose

Define el contrato del repositorio de la entidad Venta: obtención por id, listado paginado filtrado por cliente, detalle con cliente y renglones/libro en un número fijo de consultas, conteo y escritura mediante flush, sin carga perezosa.

## Requirements

### Requirement: Obtención de venta por id

El repositorio SHALL devolver la venta solicitada por su id o nulo si no existe.

#### Scenario: Venta existente

- **WHEN** se consulta el repositorio por un id de venta presente
- **THEN** devuelve la entidad Venta correspondiente

#### Scenario: Venta inexistente

- **WHEN** se consulta el repositorio por un id de venta ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Detalle de venta con precarga de relaciones

El repositorio SHALL devolver una venta con su cliente, sus renglones y el libro de cada renglón precargados en un número fijo de consultas, independiente de la cantidad de renglones.

#### Scenario: Detalle de venta sin N+1

- **WHEN** se invoca `get_con_detalle` con un id de venta
- **THEN** devuelve la venta con cliente (`joinedload`) y renglones con libro (`selectinload`) ya cargados, sin consultas adicionales por renglón

### Requirement: Listado paginado de ventas

El repositorio SHALL listar ventas aplicando `offset`/`limit`, filtro opcional por `cliente_id` y precarga de cliente y renglones.

#### Scenario: Listado paginado de ventas

- **WHEN** se solicita `get_all` con `offset`/`limit` y opcionalmente `cliente_id`
- **THEN** devuelve ventas filtradas y paginadas con relaciones precargadas

### Requirement: Conteo de ventas total y por cliente

El repositorio SHALL devolver la cantidad total de ventas y la cantidad de ventas de un cliente dado.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla venta

#### Scenario: Conteo por cliente

- **WHEN** se invoca `count` con filtro `cliente_id`
- **THEN** devuelve la cantidad de ventas de ese cliente

### Requirement: Escritura de venta mediante flush

El repositorio SHALL agregar, actualizar o eliminar una venta con `flush()` y nunca con `commit()`.

#### Scenario: Alta de venta

- **WHEN** se invoca `add` con una entidad Venta (y sus renglones) y se hace flush
- **THEN** la venta persiste en la transacción abierta sin confirmarla
