# Spec Delta

## Purpose

Actualiza el alta de venta del TP: la venta ahora descuenta stock y deja un movimiento por renglón (RN-10), y los rechazos incluyen libros dados de baja y stock insuficiente.

## REMOVED Requirements

### Requirement: La venta registra un hecho y no modifica el stock
**Reason**: el Parcial reemplaza SU-01 del TP; vender descuenta stock y deja movimientos (RN-10, RN-11).
**Migration**: el comportamiento nuevo vive en las capacidades `ventas-con-stock` y `stock-movimientos`.

## MODIFIED Requirements

### Requirement: Cliente o libro inexistente responde 409
Si el cliente o alguno de los libros no existe, o el libro está dado de baja, o el stock del libro no alcanza para la cantidad pedida, la API SHALL responder 409 con un mensaje propio, sin devolver texto interno de la base (RN-12, RN-15) y sin escrituras parciales. La inexistencia de un libro SHALL detectarse al leer su precio entre los libros vigentes, sin consultar la existencia del cliente antes de escribir.

#### Scenario: Cliente inexistente
- **WHEN** se envía `POST /ventas/` con un `cliente_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y no queda ninguna venta, renglón, descuento ni movimiento

#### Scenario: Libro inexistente
- **WHEN** se envía `POST /ventas/` con un `libro_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y no queda ninguna escritura

#### Scenario: Libro dado de baja
- **WHEN** se envía `POST /ventas/` con un libro cuyo `borrado_en` no es nulo
- **THEN** la API responde 409 y no modifica el stock

#### Scenario: Stock insuficiente
- **WHEN** se envía `POST /ventas/` pidiendo más unidades de las que el libro tiene en stock
- **THEN** la API responde 409 y no queda ninguna escritura
