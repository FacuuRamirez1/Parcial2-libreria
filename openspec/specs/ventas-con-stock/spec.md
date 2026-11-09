# ventas-con-stock Specification

## Purpose

Define el registro atómico de una venta con descuento de stock y un movimiento por renglón, los rechazos sin escrituras parciales y la invariante stock = suma de movimientos.

## Requirements

### Requirement: La venta descuenta stock y deja un movimiento por renglón
`POST /ventas` SHALL, en un único Unit of Work: leer los libros vigentes, copiar el precio de cada uno, calcular el total con `Decimal`, insertar la venta y sus renglones, descontar el stock de cada libro y agregar un movimiento negativo por renglón usando el punto único de escritura de stock, con el usuario que registra la venta y el `venta_id` de la venta creada. SHALL responder 201 con el detalle de la venta.

#### Scenario: Venta exitosa
- **WHEN** un vendedor registra una venta de 1 unidad de un libro con stock 10
- **THEN** la respuesta es 201, el libro queda con stock 9 y existe un movimiento de `cantidad = -1` ligado a esa venta

#### Scenario: Un movimiento por renglón
- **WHEN** un vendedor registra una venta con dos renglones distintos
- **THEN** se crean exactamente dos movimientos negativos, uno por cada libro

### Requirement: Rechazo atómico por stock insuficiente
Si algún libro no tiene stock suficiente para la cantidad pedida, la API SHALL responder 409 con un mensaje propio y NO SHALL persistir la venta, ni sus renglones, ni descuentos de stock, ni movimientos (RN-10).

#### Scenario: Stock insuficiente en un renglón
- **WHEN** un vendedor pide 2 unidades de un libro con stock 1
- **THEN** la respuesta es 409 y el stock del libro sigue en 1, sin venta nueva ni movimientos nuevos

#### Scenario: Venta válida e inválida mezcladas
- **WHEN** una venta incluye un renglón con stock suficiente y otro sin stock
- **THEN** la respuesta es 409 y ninguno de los dos libros cambia de stock

### Requirement: Rechazo de libros o clientes inexistentes
Si el cliente o algún libro no existe, o el libro está dado de baja, la API SHALL responder 409 con un mensaje propio y sin escrituras parciales.

#### Scenario: Cliente inexistente
- **WHEN** un vendedor registra una venta con un `cliente_id` que no existe
- **THEN** la respuesta es 409 y no queda ninguna venta, renglón ni movimiento

#### Scenario: Libro inexistente o dado de baja
- **WHEN** un vendedor registra una venta con un `libro_id` inexistente o con `borrado_en` no nulo
- **THEN** la respuesta es 409 y no queda ninguna escritura de esa petición

### Requirement: Invariante stock = suma de movimientos
Después de cada alta, reposición o venta, para cada libro SHALL cumplirse `libro.stock == suma(movimiento_stock.cantidad)` del libro. Ninguna operación SHALL romper la invariante.

#### Scenario: Invariante tras varias operaciones
- **WHEN** un libro se crea con stock inicial, se repone y se vende
- **THEN** la suma de las cantidades de sus movimientos coincide exactamente con `libro.stock`
