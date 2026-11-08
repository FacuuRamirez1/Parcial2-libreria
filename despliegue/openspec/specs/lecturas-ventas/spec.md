# lecturas-ventas Specification

## Purpose
Define el detalle de venta con cliente y renglones (con su libro) precargados, sin N+1 y con número fijo de consultas.

## Requirements

### Requirement: Detalle de venta precargado

`GET /ventas/{id}` SHALL cargar el cliente con `joinedload` y los renglones con `selectinload`, incluyendo el libro de cada renglón, en la misma operación de consulta. La respuesta MUST incluir `titulo`, `precio_unitario` y `subtotal` por renglón sin disparar carga perezosa.

#### Scenario: Venta con varios renglones

- **WHEN** se consulta `GET /ventas/{id}` de una venta con tres renglones
- **THEN** la respuesta 200 incluye los tres renglones, cada uno con `titulo`, `precio_unitario` y `subtotal`, sin consultas adicionales por renglón

#### Scenario: Venta inexistente

- **WHEN** se consulta `GET /ventas/999999`
- **THEN** la respuesta es 404 con mensaje propio

### Requirement: Conteo fijo de consultas en ventas

El número de sentencias `SELECT` ejecutadas por `GET /ventas/{id}` SHALL ser 2, independientemente de la cantidad de renglones (1 o N).

#### Scenario: Detalle con 1 vs. 3 renglones

- **WHEN** se mide `GET /ventas/{id}` para una venta con 1 renglón y para otra con 3 renglones
- **THEN** ambos requests ejecutan exactamente 2 `SELECT`
