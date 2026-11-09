# baja-logica-libros Specification

## Purpose

Define la baja lógica de un libro, su salida del catálogo, la re-alta de un ISBN ya dado de baja y el rechazo de vender o reponer un libro dado de baja.

## Requirements

### Requirement: Baja lógica de un libro
`DELETE /libros/{id}` (ADMIN) SHALL marcar el libro con `borrado_en` (fecha con zona) sin borrar la fila y SHALL responder 204. Un libro inexistente o ya dado de baja SHALL responder 404. Las ventas anteriores que lo referencian SHALL conservarse y seguir mostrando su título (RN-13).

#### Scenario: Baja de un libro vigente
- **WHEN** un administrador da de baja un libro vigente
- **THEN** la respuesta es 204, la fila sigue en la tabla con `borrado_en` no nulo y el libro ya no aparece en `GET /libros/`

#### Scenario: Baja repetida
- **WHEN** un administrador da de baja un libro ya dado de baja
- **THEN** la respuesta es 404

#### Scenario: Baja de un libro inexistente
- **WHEN** un administrador da de baja un id inexistente
- **THEN** la respuesta es 404

### Requirement: El catálogo excluye los libros dados de baja
`GET /libros/` y `GET /libros/{id}` SHALL excluir los libros con `borrado_en` no nulo. El listado SHALL no contarlos en `total` y el detalle de un libro dado de baja SHALL responder 404.

#### Scenario: Libro dado de baja fuera del listado
- **WHEN** se consulta `GET /libros/` después de dar de baja un libro
- **THEN** el libro no aparece en `items` y `total` no lo cuenta

#### Scenario: Detalle de un libro dado de baja
- **WHEN** se consulta `GET /libros/{id}` de un libro dado de baja
- **THEN** la respuesta es 404

### Requirement: Re-alta de un ISBN dado de baja
`POST /libros` SHALL aceptar el mismo ISBN de un libro dado de baja y responder 201 con un libro nuevo vigente (el índice único parcial solo considera los vigentes). Un segundo libro vigente con el mismo ISBN SHALL responder 409 sin texto interno de la base (RN-01).

#### Scenario: Re-alta del mismo ISBN
- **WHEN** un administrador da de baja un libro y crea otro con el mismo ISBN
- **THEN** la respuesta es 201 y ambos registros conviven (uno dado de baja y uno vigente)

#### Scenario: Segundo libro vigente con el mismo ISBN
- **WHEN** ya existe un libro vigente con un ISBN y se intenta crear otro con ese ISBN
- **THEN** la respuesta es 409 con un mensaje propio

### Requirement: Un libro dado de baja no se vende ni se repone
`POST /ventas` SHALL rechazar con 409 cualquier renglón que apunte a un libro dado de baja, y `POST /libros/{id}/reponer` SHALL responder 409 para un libro dado de baja. En ambos casos NO SHALL quedar escrituras de stock ni de movimientos.

#### Scenario: Venta con libro dado de baja
- **WHEN** un vendedor intenta vender un libro con `borrado_en` no nulo
- **THEN** la respuesta es 409 y no se crea la venta ni se modifica el stock

#### Scenario: Reposición de un libro dado de baja
- **WHEN** un administrador repone un libro con `borrado_en` no nulo
- **THEN** la respuesta es 409 y no se agrega ningún movimiento
