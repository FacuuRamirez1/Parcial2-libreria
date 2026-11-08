# Spec Delta

## Purpose

Define el alta de una venta con sus renglones: validación del contrato, precio copiado desde el libro, total y subtotales calculados por el servidor, fecha del servidor y respuesta con el título de cada libro.

## ADDED Requirements

### Requirement: Contrato de alta de venta
`POST /ventas/` SHALL aceptar `cliente_id` y `renglones`, donde cada renglón contiene `libro_id` y `cantidad`. El cuerpo NO SHALL aceptar `precio_unitario`, `subtotal`, `total` ni `fecha`; cualquier campo desconocido SHALL responder 422 (`extra="forbid"`).

#### Scenario: Precio enviado en la entrada
- **WHEN** se envía `POST /ventas/` con `precio_unitario` en un renglón
- **THEN** la API responde 422 y no crea la venta

#### Scenario: Total enviado en la entrada
- **WHEN** se envía `POST /ventas/` con `total` en el cuerpo
- **THEN** la API responde 422 y no crea la venta

### Requirement: Validación del contrato de venta
El DTO de entrada SHALL validar antes de escribir que haya al menos un renglón, que no se repita un mismo `libro_id` y que cada `cantidad` sea mayor que cero (RN-05). Toda violación SHALL responder 422 y NO SHALL crear la venta.

#### Scenario: Venta sin renglones
- **WHEN** se envía `POST /ventas/` con `renglones = []`
- **THEN** la API responde 422 y no crea la venta

#### Scenario: Libro repetido en los renglones
- **WHEN** se envía `POST /ventas/` con el mismo `libro_id` en dos renglones
- **THEN** la API responde 422 y no crea la venta

#### Scenario: Cantidad no positiva
- **WHEN** se envía `POST /ventas/` con un renglón de `cantidad = 0`
- **THEN** la API responde 422 y no crea la venta

### Requirement: Precio copiado y total calculado por el servidor
Al registrar la venta, el servidor SHALL leer el precio vigente de cada libro y copiarlo en `renglon_venta.precio_unitario` (RN-06). El `total` de la venta SHALL ser la suma de `cantidad × precio_unitario` de todos los renglones, calculada con `Decimal` y sin aceptar el total desde la entrada (RN-07). La `fecha` SHALL ser la del servidor al crear la venta.

#### Scenario: Total de dos renglones
- **WHEN** se registra una venta con un renglón de 2 unidades de un libro de precio 25.00 y otro de 1 unidad de un libro de precio 10.50
- **THEN** la respuesta 201 informa `precio_unitario` 25.00 y 10.50, subtotales 50.00 y 10.50, y `total` 60.50

#### Scenario: El precio enviado por el cliente no se usa
- **WHEN** se registra una venta de un libro cuyo precio en la base es 25.00
- **THEN** el `precio_unitario` persistido y devuelto es 25.00

### Requirement: Respuesta del alta con título, precio unitario y subtotal
La respuesta 201 SHALL incluir `id`, `cliente_id`, `fecha`, `total` y, por cada renglón, `titulo`, `precio_unitario`, `cantidad` y `subtotal`. El `subtotal` SHALL ser `cantidad × precio_unitario` calculado por el servidor.

#### Scenario: Detalle de los renglones en la respuesta
- **WHEN** se registra una venta válida
- **THEN** cada renglón de la respuesta 201 incluye el `titulo` del libro, su `precio_unitario` y su `subtotal`

#### Scenario: Título en las lecturas de ventas
- **WHEN** se consulta `GET /ventas/` o `GET /ventas/{id}` de una venta existente
- **THEN** cada renglón incluye `titulo`, `precio_unitario` y `subtotal`

### Requirement: Cliente o libro inexistente responde 409
Si el cliente o alguno de los libros no existe, la API SHALL responder 409 con un mensaje propio, sin devolver texto interno de la base (RN-12). La inexistencia de un libro SHALL detectarse al leer su precio, sin consultar la existencia del cliente antes de escribir.

#### Scenario: Cliente inexistente
- **WHEN** se envía `POST /ventas/` con un `cliente_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y no queda ninguna venta ni renglón persistidos

#### Scenario: Libro inexistente
- **WHEN** se envía `POST /ventas/` con un `libro_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y no queda ninguna venta ni renglón persistidos

### Requirement: La venta registra un hecho y no modifica el stock
Las ventas NO SHALL modificarse después de creadas: el módulo NO expone `PATCH /ventas/{id}` (RN-08). Registrar una venta NO SHALL modificar `libro.stock` (SU-01).

#### Scenario: Sin modificación de ventas
- **WHEN** se intenta `PATCH /ventas/{id}`
- **THEN** la API no expone esa operación

#### Scenario: El stock no cambia al vender
- **WHEN** se registra una venta de un libro con `stock = 10`
- **THEN** el libro sigue con `stock = 10` después de la venta
