# stock-movements-data Specification

## Purpose

Define la tabla de movimientos de stock del catálogo y la garantía, impuesta por la propia base, de que sus filas solo se agregan: ninguna se modifica ni se borra, y los errores se compensan con otro movimiento.

## Requirements

### Requirement: Tabla movimiento_stock
El esquema SHALL incluir la tabla `movimiento_stock` con `id`, `libro_id` (FK a `libro`, obligatoria), `venta_id` (FK a `venta`, nula), `usuario_id` (FK a `usuario`, obligatoria), `cantidad` (entero), `motivo` (texto, máximo 120) y `cuando` (`timestamptz`). Cada FK SHALL tener un índice propio.

#### Scenario: Movimiento sin venta
- **WHEN** se guarda un movimiento de alta o reposición con `venta_id` nulo, un libro y un usuario existentes
- **THEN** la base acepta la escritura

#### Scenario: Movimiento con libro inexistente
- **WHEN** se intenta guardar un movimiento con un `libro_id` que no existe
- **THEN** la base rechaza la escritura por violación de la clave foránea

#### Scenario: Índices de las claves foráneas
- **WHEN** se listan los índices de `movimiento_stock`
- **THEN** hay uno sobre `libro_id`, otro sobre `venta_id` y otro sobre `usuario_id`

### Requirement: Cantidad del movimiento distinta de cero
La base SHALL rechazar, mediante un CHECK, todo movimiento con `cantidad = 0`. Las cantidades positivas (entradas) y negativas (salidas) SHALL aceptarse.

#### Scenario: Cantidad cero
- **WHEN** se intenta guardar un movimiento con `cantidad = 0`
- **THEN** la base rechaza la escritura por violación del CHECK

#### Scenario: Salida por venta
- **WHEN** se guarda un movimiento con `cantidad = -2` ligado a una venta existente
- **THEN** la base acepta la escritura

### Requirement: Movimientos de solo agregado
La base SHALL rechazar cualquier `UPDATE` o `DELETE` sobre `movimiento_stock`, venga de la aplicación o de una sesión directa de `psql` (RN-12). La garantía SHALL vivir en la base, instalada por una migración, y SHALL dejar intactas las filas afectadas.

#### Scenario: UPDATE desde psql
- **WHEN** se ejecuta en `psql` un `UPDATE movimiento_stock SET cantidad = 99` sobre una fila existente
- **THEN** la sentencia falla con un error que indica que la tabla es de solo agregado y la fila conserva su valor

#### Scenario: DELETE desde psql
- **WHEN** se ejecuta en `psql` un `DELETE FROM movimiento_stock` sobre una fila existente
- **THEN** la sentencia falla con el mismo error y la fila sigue existiendo

#### Scenario: Agregar sigue permitido
- **WHEN** se inserta un movimiento válido con el trigger instalado
- **THEN** la base acepta la escritura

### Requirement: Navegación de movimientos en ambos extremos
Un movimiento SHALL dar acceso a su libro, a su venta (o ninguna) y a su usuario; un libro, una venta y un usuario SHALL dar acceso a la colección de sus movimientos. Toda navegación SHALL requerir precarga explícita.

#### Scenario: Movimientos de un libro
- **WHEN** se lee un libro precargando sus movimientos
- **THEN** se obtiene la colección de sus movimientos y cada uno da acceso al mismo libro

#### Scenario: Movimiento sin venta precargada
- **WHEN** se lee un movimiento de alta precargando su venta
- **THEN** la venta del movimiento es nula
