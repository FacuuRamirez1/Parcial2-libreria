# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo ventas, separados de las tablas `venta` y `renglon_venta`. `VentaCreate` no incluye precios ni totales (el servidor los calcula).

## ADDED Requirements

### Requirement: VentaCreate
DTO de entrada para crear una venta. Campos: `cliente_id` (int), `renglones` (lista de `{libro_id: int, cantidad: int}`). **Sin** `precio_unitario`, `subtotal` ni `total`. `ConfigDict(extra="forbid")`.

#### Scenario: Sin precios en la entrada
- **WHEN** se envía `POST /ventas/` con `precio_unitario` en un renglón
- **THEN** la API responde 422 (`extra="forbid"`)

### Requirement: VentaRead
DTO de salida. Campos: `id` (int), `cliente_id` (int), `fecha` (datetime con zona horaria), `total` (Decimal), `renglones` (lista de `{libro_id, cantidad, precio_unitario, subtotal}`).
