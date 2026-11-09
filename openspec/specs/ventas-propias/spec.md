# ventas-propias Specification

## Purpose

Define las lecturas de ventas propias de un cliente autenticado y la decisión de dueño o personal en el detalle de una venta.

## Requirements

### Requirement: Mis ventas
`GET /mis-ventas` SHALL exigir solo autenticación (sin rol de personal) y SHALL devolver, con el envoltorio `{items,total,page,size,pages}`, únicamente las ventas del cliente asociado al usuario actual (`cliente.usuario_id == usuario.id`). Si el usuario no tiene ficha de cliente, SHALL devolver una página vacía con `total = 0`. `page` y `size` SHALL validarse como en el resto de los listados.

#### Scenario: Cliente con ventas
- **WHEN** un cliente autenticado con ventas propias pide `GET /mis-ventas?page=1&size=20`
- **THEN** la respuesta es 200 con solo sus ventas y `total` igual a la cantidad de esas ventas

#### Scenario: Usuario sin ficha de cliente
- **WHEN** un usuario autenticado sin `cliente` asociado pide `GET /mis-ventas`
- **THEN** la respuesta es 200 con `items: []` y `total: 0`

#### Scenario: Sin sesión
- **WHEN** se pide `GET /mis-ventas` sin cookie
- **THEN** la respuesta es 401

### Requirement: Detalle de venta para personal o dueño
`GET /ventas/{id}` SHALL exigir solo autenticación y la decisión SHALL tomarla el servicio: SHALL permitir la lectura si el usuario tiene un rol vigente `VENDEDOR` o `ADMIN`, o si es el cliente dueño de la venta (`venta.cliente.usuario_id == usuario.id`). En cualquier otro caso SHALL responder 403. Una venta inexistente SHALL responder 404.

#### Scenario: Cliente dueño de la venta
- **WHEN** el cliente dueño de una venta pide `GET /ventas/{id}`
- **THEN** la respuesta es 200 con el detalle

#### Scenario: Cliente ajeno a la venta
- **WHEN** un cliente autenticado que no es dueño de la venta pide `GET /ventas/{id}`
- **THEN** la respuesta es 403

#### Scenario: Personal con rol vigente
- **WHEN** un vendedor o administrador autenticado pide `GET /ventas/{id}`
- **THEN** la respuesta es 200 con el detalle

#### Scenario: Venta inexistente
- **WHEN** un usuario autenticado pide `GET /ventas/999999`
- **THEN** la respuesta es 404

### Requirement: Detalle de venta con libro dado de baja
`GET /ventas/{id}` SHALL seguir mostrando el título del libro aunque el libro esté dado de baja, con la misma precarga y el mismo número fijo de consultas.

#### Scenario: Venta vieja de un libro dado de baja
- **WHEN** se consulta el detalle de una venta cuyo libro fue dado de baja
- **THEN** la respuesta es 200 e incluye el título del libro
