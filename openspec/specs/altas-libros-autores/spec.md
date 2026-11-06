# altas-libros-autores Specification

## Purpose
Define el alta de un libro junto con sus autorías (`rol` y `orden`) en una sola operación, con validación estricta del contrato y traducción de los rechazos de la base a respuestas HTTP propias.

## Requirements

### Requirement: Alta de libro con autores
`POST /libros/` SHALL aceptar `isbn`, `titulo`, `precio`, `stock_inicial`, `editorial_id`, `genero_id` obligatorio y una lista `autores` de elementos `{autor_id, rol, orden}`. El cuerpo SHALL rechazar campos desconocidos con 422 (`extra="forbid"`). La lista `autores` SHALL ser opcional y, si no se envía o está vacía, el libro se crea sin autorías.

#### Scenario: Alta con dos autores
- **WHEN** se envía `POST /libros/` con dos elementos en `autores`, cada uno con su `autor_id`, `rol` y `orden`
- **THEN** la API responde 201 y quedan persistidas la fila de `libro` y las dos filas de `libro_autor` asociadas a ese libro

#### Scenario: Alta sin autores
- **WHEN** se envía `POST /libros/` sin el campo `autores`
- **THEN** la API responde 201 y el libro queda creado sin filas en `libro_autor`

#### Scenario: Campo desconocido en la entrada
- **WHEN** se envía `POST /libros/` con un campo no previsto en el contrato
- **THEN** la API responde 422 sin intentar escribir en la base

### Requirement: Validación del contrato de alta de libro
El DTO de entrada SHALL validar antes de escribir que `precio` sea mayor que cero, que `stock_inicial` sea mayor o igual que cero, que `rol` pertenezca a `autor`, `coautor`, `traductor` o `ilustrador`, que `orden` sea mayor o igual que uno y que no se repita un mismo `autor_id` dentro de `autores`. Toda violación SHALL responder 422.

#### Scenario: Precio no positivo
- **WHEN** se envía `POST /libros/` con `precio = 0`
- **THEN** la API responde 422 y no se escribe ningún libro

#### Scenario: Stock inicial negativo
- **WHEN** se envía `POST /libros/` con `stock_inicial = -1`
- **THEN** la API responde 422 y no se escribe ningún libro

#### Scenario: Rol fuera de la lista permitida
- **WHEN** se envía `POST /libros/` con un autor cuyo `rol` es `editor`
- **THEN** la API responde 422 y no se escribe ningún libro

#### Scenario: Orden inválido
- **WHEN** se envía `POST /libros/` con un autor cuyo `orden` es 0
- **THEN** la API responde 422 y no se escribe ningún libro

#### Scenario: Autor repetido en la lista
- **WHEN** se envía `POST /libros/` con el mismo `autor_id` en dos elementos de `autores`
- **THEN** la API responde 422 y no se escribe ningún libro

### Requirement: Género obligatorio en el alta
`genero_id` SHALL ser obligatorio en el contrato de alta (`POST /libros/`), por decisión del proyecto, aunque la columna `libro.genero_id` admita NULL para filas existentes. Cuando se envíe, SHALL referenciar un género existente.

#### Scenario: Libro sin género
- **WHEN** se envía `POST /libros/` sin `genero_id` y el resto del contrato es válido
- **THEN** la API responde 422 y no se escribe ningún libro

#### Scenario: Género inexistente
- **WHEN** se envía `POST /libros/` con un `genero_id` que no corresponde a ningún género
- **THEN** la API responde 409 con un mensaje propio y no queda ningún libro ni autoría persistidos

### Requirement: Errores de integridad del alta de libro
Cuando la base rechace el alta por ISBN duplicado, por una clave foránea inexistente o por una restricción CHECK, la API SHALL responder 409 con un mensaje propio. La aplicación NO SHALL consultar previamente si los ids existen ni SHALL devolver nombres de tablas, restricciones, columnas, mensajes del driver o trazas.

#### Scenario: ISBN repetido
- **WHEN** se envía `POST /libros/` con un `isbn` ya registrado
- **THEN** la API responde 409 con un mensaje propio y sin texto interno de la base

#### Scenario: Editorial inexistente
- **WHEN** se envía `POST /libros/` con un `editorial_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y sin texto interno de la base

#### Scenario: Autor inexistente
- **WHEN** se envía `POST /libros/` con un `autor_id` que no existe
- **THEN** la API responde 409 con un mensaje propio y ninguna de las filas de `libro_autor` queda persistida

### Requirement: Atomicidad del alta de libro
El libro y sus autorías SHALL escribirse en una única transacción. Si cualquier escritura es rechazada, la transacción SHALL revertirse por completo y no SHALL quedar un libro sin sus autorías ni autorías huérfanas.

#### Scenario: Reversión completa ante autor inválido
- **WHEN** se envía `POST /libros/` con un libro válido y un `autor_id` inexistente
- **THEN** la API responde 409 y no existe ninguna fila nueva en `libro` ni en `libro_autor`
