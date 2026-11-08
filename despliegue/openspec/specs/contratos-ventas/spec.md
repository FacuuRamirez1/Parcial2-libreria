# contratos-ventas Specification

## Purpose
Define los DTOs de entrada y salida del módulo ventas, que nunca aceptan precios ni totales del cliente.

## Requirements

### Requirement: VentaCreate

El DTO de entrada `VentaCreate` SHALL declarar `cliente_id` (int) y `renglones` (list[RenglonVentaCreate]) obligatorios, con `ConfigDict(extra="forbid")`. MUST rechazar una lista vacía y MUST rechazar libros repetidos entre renglones. MUST NOT aceptar `fecha`, `total`, `precio_unitario` ni `subtotal`.

#### Scenario: Venta válida

- **WHEN** se envía `POST /ventas/` con `cliente_id` y al menos un renglón con `libro_id` y `cantidad`
- **THEN** la API responde 201 con el `VentaRead` calculado en el servidor

#### Scenario: Precio enviado por el cliente

- **WHEN** se envía `POST /ventas/` con `precio_unitario` o `total` en un renglón o en la venta
- **THEN** la API responde 422 por `extra="forbid"`

#### Scenario: Sin renglones

- **WHEN** se envía `POST /ventas/` con `renglones = []`
- **THEN** la API responde 422

#### Scenario: Libro repetido

- **WHEN** se envía `POST /ventas/` con el mismo `libro_id` en dos renglones
- **THEN** la API responde 422

### Requirement: RenglonVentaRead

El DTO de salida `RenglonVentaRead` SHALL exponer `libro_id` (int), `titulo` (str), `cantidad` (int), `precio_unitario` (Decimal) y `subtotal` (Decimal), con `from_attributes=True`. El `titulo` proviene del libro asociado y el `subtotal` del cálculo del servidor.

#### Scenario: Representación de un renglón

- **WHEN** se consulta una venta creada
- **THEN** cada renglón incluye `libro_id`, `titulo`, `cantidad`, `precio_unitario` y `subtotal = cantidad * precio_unitario`

### Requirement: VentaRead

El DTO de salida `VentaRead` SHALL exponer `id` (int), `cliente_id` (int), `fecha` (datetime), `total` (Decimal) y `renglones` (list[RenglonVentaRead]).

#### Scenario: Representación de una venta

- **WHEN** se consulta `GET /ventas/{id}` de una venta existente
- **THEN** el cuerpo contiene `id`, `cliente_id`, `fecha`, `total` y `renglones`
