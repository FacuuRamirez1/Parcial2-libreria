# contratos-libros Specification

## Purpose
Define los DTOs de entrada y salida del módulo libros, incluida la reposición de stock, con validación estricta de entrada (`extra="forbid"`).

## Requirements

### Requirement: LibroCreate

El DTO de entrada `LibroCreate` SHALL declarar `isbn` (str, `max_length=17`), `titulo` (str, `max_length=255`), `precio` (Decimal, `> 0`), `stock_inicial` (int, `>= 0`), `editorial_id` (int) y `genero_id` (int) obligatorios, y `autores` (list[LibroAutorCreate]) opcional con `default_factory=list`. MUST usar `ConfigDict(extra="forbid")` y MUST rechazar autores repetidos.

#### Scenario: Alta válida

- **WHEN** se envía `POST /libros/` con `isbn`, `titulo`, `precio`, `stock_inicial`, `editorial_id` y `genero_id`
- **THEN** la API responde 201 con el `LibroRead` creado y `stock = stock_inicial`

#### Scenario: genero_id ausente

- **WHEN** se envía `POST /libros/` sin `genero_id`
- **THEN** la API responde 422 porque el campo es obligatorio

#### Scenario: Precio no positivo

- **WHEN** se envía `POST /libros/` con `precio = 0`
- **THEN** la API responde 422

#### Scenario: Autor repetido

- **WHEN** se envía `POST /libros/` con el mismo `autor_id` dos veces en `autores`
- **THEN** la API responde 422

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /libros/` con un campo no declarado
- **THEN** la API responde 422

### Requirement: LibroUpdate

El DTO de entrada `LibroUpdate` SHALL permitir `isbn` (`max_length=17`), `titulo` (`max_length=255`), `precio` (Decimal, `> 0`), `editorial_id` (int) y `genero_id` (int) todos opcionales. MUST rechazar `stock` y cualquier otro campo no declarado mediante `ConfigDict(extra="forbid")`; el stock solo se modifica por venta o reposición.

#### Scenario: Actualización completa del contrato

- **WHEN** se envía `PATCH /libros/{id}` con `isbn`, `titulo`, `precio`, `editorial_id` y `genero_id`
- **THEN** la API responde 200 con los cinco campos actualizados y el `stock` sin cambios

#### Scenario: Stock no editable

- **WHEN** se envía `PATCH /libros/{id}` con `stock`
- **THEN** la API responde 422

#### Scenario: Precio no positivo

- **WHEN** se envía `PATCH /libros/{id}` con `precio = -1`
- **THEN** la API responde 422

### Requirement: ReponerStockRequest

El DTO de entrada `ReponerStockRequest` SHALL declarar `cantidad` (int, `> 0`) y `usuario_id` (int) obligatorios, con `ConfigDict(extra="forbid")`. El `usuario_id` identifica quién registra el movimiento de stock.

#### Scenario: Reposición válida

- **WHEN** se envía `PATCH /libros/{id}/reponer-stock` con `cantidad` y `usuario_id`
- **THEN** la API responde 200 con el libro y el `stock` incrementado en `cantidad`

#### Scenario: usuario_id ausente

- **WHEN** se envía `PATCH /libros/{id}/reponer-stock` sin `usuario_id`
- **THEN** la API responde 422

#### Scenario: Cantidad no positiva

- **WHEN** se envía `PATCH /libros/{id}/reponer-stock` con `cantidad = 0`
- **THEN** la API responde 422

#### Scenario: Campo extra rechazado

- **WHEN** se envía `PATCH /libros/{id}/reponer-stock` con un campo no declarado
- **THEN** la API responde 422

### Requirement: LibroRead

El DTO de salida `LibroRead` SHALL exponer `id`, `isbn`, `titulo`, `precio`, `stock`, `borrado_en`, `editorial_id` y `genero_id`, con `from_attributes=True`.

#### Scenario: Representación de salida

- **WHEN** se consulta `GET /libros/{id}` de un libro existente
- **THEN** el cuerpo contiene los ocho campos de `LibroRead` y ningún campo interno de la tabla
