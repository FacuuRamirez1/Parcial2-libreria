# transacciones-venta Specification

## Purpose
Garantizar que el alta de una venta y sus renglones se confirme como una unidad atómica, de modo que una venta exitosa quede disponible después de responder y una fallida no deje datos parciales.

## Requirements

### Requirement: Confirmación atómica y persistencia del alta de venta
`POST /ventas/` SHALL confirmar en una única transacción la venta y todos sus renglones antes de devolver la respuesta 201. Una venta devuelta como creada SHALL poder consultarse después con `GET /ventas/{id}`.

#### Scenario: La venta persiste después de la respuesta
- **WHEN** se registra una venta y la API responde 201
- **THEN** `GET /ventas/{id}` devuelve la misma venta con sus renglones

#### Scenario: Los renglones pertenecen a la venta creada
- **WHEN** se registra una venta con dos renglones y la API responde 201
- **THEN** ambos renglones existen asociados al `venta_id` de esa venta

### Requirement: Reversión completa ante rechazo de la base
Si la base rechaza la inserción de la venta o de cualquiera de sus renglones, la transacción SHALL revertirse por completo: NO SHALL quedar una venta sin renglones ni renglones sin venta, y la API SHALL responder el código de error correspondiente (409) con un mensaje propio.

#### Scenario: Cliente inexistente no deja venta parcial
- **WHEN** se envía `POST /ventas/` con un `cliente_id` inexistente
- **THEN** la API responde 409 y no queda ninguna fila nueva en `venta` ni en `renglon_venta`

#### Scenario: Libro inexistente no deja venta parcial
- **WHEN** se envía `POST /ventas/` con un `libro_id` inexistente
- **THEN** la API responde 409 y no queda ninguna fila nueva en `venta` ni en `renglon_venta`

### Requirement: La sesión de la petición no confirma por sí sola
La confirmación de la transacción SHALL ser explícita en el alta de venta. Una sesión que solo leyó datos o que terminó por un error NO SHALL dejar escrituras confirmadas.

#### Scenario: Petición fallida sin escrituras confirmadas
- **WHEN** una petición de alta de venta termina con error antes de completar los renglones
- **THEN** la base no conserva ninguna escritura de esa petición
