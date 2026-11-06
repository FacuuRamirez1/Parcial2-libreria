# Spec Delta

## Purpose

Define el esquema de ventas y de sus renglones, con montos en decimal exacto, fecha con zona horaria y las garantías de la base sobre cantidades, precios y referencias a clientes y libros.

## ADDED Requirements

### Requirement: Tabla venta
El esquema SHALL incluir la tabla `venta` con las columnas `id` (clave primaria entera generada por la base), `cliente_id` (obligatoria, FK a `cliente.id`, con índice propio), `fecha` y `total`, ambas obligatorias.

#### Scenario: Venta de un cliente inexistente
- **WHEN** se intenta guardar una venta con un `cliente_id` que no corresponde a ningún cliente
- **THEN** la base rechaza la escritura por violación de clave foránea

### Requirement: Fecha de venta con zona horaria
`venta.fecha` SHALL almacenarse como marca de tiempo con zona horaria (`TIMESTAMP WITH TIME ZONE`). Cuando no se indica, SHALL tomar el instante actual en UTC al crear la venta.

#### Scenario: Tipo de la columna fecha
- **WHEN** se inspecciona el DDL de `venta` para PostgreSQL
- **THEN** `fecha` es `TIMESTAMP WITH TIME ZONE NOT NULL`

#### Scenario: Fecha por defecto
- **WHEN** se crea una venta sin indicar `fecha`
- **THEN** la venta queda con una fecha consciente de zona horaria igual al instante de creación en UTC

### Requirement: Total de la venta exacto y no negativo
`venta.total` SHALL ser decimal exacto `NUMERIC(12,2)` (nunca coma flotante) y la base SHALL rechazar un total negativo.

#### Scenario: Tipo de la columna total
- **WHEN** se inspecciona el DDL de `venta` para PostgreSQL
- **THEN** `total` es `NUMERIC(12, 2) NOT NULL`

#### Scenario: Total negativo rechazado
- **WHEN** se intenta guardar una venta con `total = -0.01`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

### Requirement: Tabla renglon_venta
El esquema SHALL incluir la tabla `renglon_venta` con las columnas `id` (clave primaria entera generada por la base), `venta_id` (FK a `venta.id`), `libro_id` (FK a `libro.id`), `cantidad` (entero) y `precio_unitario` (`NUMERIC(10,2)`), todas obligatorias, con un índice propio en `venta_id` y otro en `libro_id`.

#### Scenario: Renglón con libro inexistente
- **WHEN** se intenta guardar un renglón con un `libro_id` que no corresponde a ningún libro
- **THEN** la base rechaza la escritura por violación de clave foránea

#### Scenario: Tipo de la columna precio_unitario
- **WHEN** se inspecciona el DDL de `renglon_venta` para PostgreSQL
- **THEN** `precio_unitario` es `NUMERIC(10, 2) NOT NULL`

### Requirement: Cantidad y precio unitario positivos
La base SHALL rechazar en `renglon_venta` una `cantidad` menor o igual a cero y un `precio_unitario` menor o igual a cero.

#### Scenario: Cantidad cero
- **WHEN** se intenta guardar un renglón con `cantidad = 0`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

#### Scenario: Precio unitario cero
- **WHEN** se intenta guardar un renglón con `precio_unitario = 0`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

### Requirement: Renglones creados junto con su venta
Los renglones SHALL ser parte de su venta (composición): al guardar una venta nueva con renglones agregados a su colección, todos se guardan en la misma operación y quedan asociados a esa venta, sin un alta separada (RN-04).

#### Scenario: Venta con dos renglones
- **WHEN** se agrega a la sesión una venta nueva cuya colección de renglones tiene dos elementos y se confirma
- **THEN** se insertan la venta y los dos renglones, y cada renglón tiene el `venta_id` de esa venta

### Requirement: Navegación de ventas en ambos extremos
Una venta SHALL exponer su cliente y la colección de sus renglones (ordenada por `id`); cada renglón SHALL exponer su venta y su libro; un libro SHALL exponer los renglones en que aparece.

#### Scenario: Detalle de venta precargado
- **WHEN** se lee una venta con su cliente y sus renglones (y el libro de cada renglón) precargados
- **THEN** se accede al cliente, a cada renglón y a su libro sin emitir sentencias SQL adicionales
