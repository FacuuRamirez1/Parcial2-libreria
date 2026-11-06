# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo libros, separados de la tabla `libro`, con validación estricta de entrada (`extra="forbid"`). `LibroCreate` incluye `stock_inicial`; `LibroUpdate` no incluye `stock`.

## ADDED Requirements

### Requirement: LibroCreate
DTO de entrada para crear un libro. Campos: `isbn` (str, max_length=17), `titulo` (str, max_length=255), `precio` (Decimal), `stock_inicial` (int), `editorial_id` (int), `genero_id` (int | None, opcional). `ConfigDict(extra="forbid")`.

#### Scenario: stock_inicial requerido
- **WHEN** se envía `POST /libros/` sin `stock_inicial`
- **THEN** la API responde 422

### Requirement: LibroUpdate
DTO de entrada para actualizar un libro. Campos opcionales: `isbn`, `titulo`, `precio`, `editorial_id`, `genero_id`. **No** incluye `stock`. `ConfigDict(extra="forbid")`.

#### Scenario: stock no editable vía PATCH
- **WHEN** se envía `PATCH /libros/{id}` con campo `stock`
- **THEN** la API responde 422 (`extra="forbid"` o campo ignorado)

### Requirement: ReponerStockRequest
DTO de entrada para reponer stock de un libro. Campo: `cantidad` (int, > 0). `ConfigDict(extra="forbid")`.

### Requirement: LibroRead
DTO de salida. Campos: `id` (int), `isbn` (str), `titulo` (str), `precio` (Decimal), `stock` (int), `borrado_en` (datetime | None), `editorial_id` (int), `genero_id` (int | None).
