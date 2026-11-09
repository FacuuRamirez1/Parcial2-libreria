# stock-movimientos Specification

## Purpose

Define el punto único de escritura del stock de un libro y las operaciones que lo usan: alta con stock inicial, reposición, venta e historial de movimientos. Ninguna otra vía puede cambiar `libro.stock`.

## Requirements

### Requirement: Punto único de escritura de stock
Todo cambio de `libro.stock` SHALL ocurrir en una única función que, en el mismo paso, actualice `libro.stock` y agregue la fila correspondiente en `movimiento_stock` con `libro_id`, `usuario_id`, `cantidad` (positiva o negativa, nunca cero), `motivo`, `venta_id` opcional y `cuando`. El alta del libro, la reposición y la venta SHALL usar esa función; ningún otro código SHALL asignar `libro.stock` (RN-11).

#### Scenario: Alta con stock inicial
- **WHEN** un administrador crea un libro con `stock_inicial = 4`
- **THEN** el libro queda con `stock = 4` y existe un movimiento de `cantidad = 4` con motivo "Stock inicial" y el usuario que lo creó

#### Scenario: Stock inicial cero
- **WHEN** un administrador crea un libro con `stock_inicial = 0`
- **THEN** el libro queda con `stock = 0` y no se crea ningún movimiento (no se admite `cantidad = 0`)

#### Scenario: Ninguna otra escritura de stock
- **WHEN** se revisa el código de la aplicación
- **THEN** la asignación de `libro.stock` aparece solo en la función de movimiento

### Requirement: Reposición de stock
`POST /libros/{id}/reponer` (ADMIN) SHALL aceptar solo `cantidad` (entero mayor que cero, `extra="forbid"`) y, en un solo Unit of Work, sumar la cantidad al stock y agregar un movimiento positivo con motivo "Reposición" y el usuario que repone. SHALL responder 200 con el detalle del libro actualizado; un libro inexistente SHALL responder 404 y uno dado de baja SHALL responder 409 (RN-13).

#### Scenario: Reposición válida
- **WHEN** un administrador repone 3 ejemplares de un libro con stock 2
- **THEN** la respuesta es 200 con `stock = 5` y queda un movimiento de `cantidad = 3` con motivo "Reposición"

#### Scenario: Cantidad no positiva
- **WHEN** un administrador envía `{"cantidad": 0}` o `{"cantidad": -1}`
- **THEN** la respuesta es 422 y el stock no cambia

#### Scenario: Reposición de un libro dado de baja
- **WHEN** un administrador repone un libro con `borrado_en` no nulo
- **THEN** la respuesta es 409 y no se agrega ningún movimiento

#### Scenario: Reposición de un libro inexistente
- **WHEN** un administrador repone un libro con un id que no existe
- **THEN** la respuesta es 404

### Requirement: Historial de movimientos de un libro
`GET /libros/{id}/movimientos` (ADMIN) SHALL devolver 200 con la lista de movimientos del libro ordenada por id, cada uno con `id`, `libro_id`, `venta_id`, `usuario_id`, `cantidad`, `motivo` y `cuando`. Un libro inexistente SHALL responder 404. El historial SHALL incluir movimientos de alta, reposición y venta, aunque el libro esté dado de baja.

#### Scenario: Historial tras alta, reposición y venta
- **WHEN** un libro se crea con stock inicial, se repone y luego se vende
- **THEN** `GET /libros/{id}/movimientos` devuelve tres movimientos: el alta positiva, la reposición positiva y la venta negativa

#### Scenario: Libro inexistente
- **WHEN** un administrador pide los movimientos de un id inexistente
- **THEN** la respuesta es 404

### Requirement: El stock no se edita por PATCH
`PATCH /libros/{id}` NO SHALL aceptar el campo `stock`; por `extra="forbid"` un cuerpo con `stock` SHALL responder 422 y el stock SHALL quedar sin cambios (RN-11).

#### Scenario: PATCH con stock
- **WHEN** un administrador envía `PATCH /libros/1` con `{"stock": 99}`
- **THEN** la respuesta es 422 y el stock del libro no cambia

#### Scenario: PATCH de otros campos
- **WHEN** un administrador envía `PATCH /libros/1` con `{"precio": "30000.00"}`
- **THEN** la respuesta es 200 con el precio actualizado y el stock intacto
