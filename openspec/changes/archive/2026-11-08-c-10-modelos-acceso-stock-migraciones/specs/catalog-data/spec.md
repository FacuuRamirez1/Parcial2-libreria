# Spec Delta

## MODIFIED Requirements

### Requirement: Tabla libro con ISBN único
El esquema SHALL incluir la tabla `libro` con las columnas `id`, `isbn`, `titulo`, `precio`, `stock`, `editorial_id`, `genero_id` y `borrado_en`. `isbn` SHALL ser `VARCHAR(17)` obligatorio (ISBN-13 con guiones) y `titulo` `VARCHAR(255)` obligatorio; `stock` entero obligatorio. El `isbn` SHALL ser único solo entre los libros vigentes (`borrado_en IS NULL`), mediante un índice único parcial que reemplaza al UNIQUE común (RN-01, DD-09).

#### Scenario: ISBN repetido
- **WHEN** se intenta guardar un libro vigente con un `isbn` que ya tiene otro libro vigente
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: ISBN de un libro dado de baja
- **WHEN** existe un libro con `isbn = '978-950-00-0001-1'` y `borrado_en` con fecha, y se guarda un libro vigente con el mismo `isbn`
- **THEN** la base acepta la escritura y ambas filas conviven

#### Scenario: Sin UNIQUE común sobre el ISBN
- **WHEN** se inspeccionan las restricciones e índices de `libro`
- **THEN** no existe la restricción `uq_libro_isbn` y existe un índice único sobre `isbn` con la condición `borrado_en IS NULL`

#### Scenario: Tipo de las columnas de texto de libro
- **WHEN** se inspecciona el DDL de `libro` para PostgreSQL
- **THEN** `isbn` es `VARCHAR(17) NOT NULL` y `titulo` es `VARCHAR(255) NOT NULL`

#### Scenario: ISBN más largo que la columna
- **WHEN** se intenta guardar directamente en la base un libro con un `isbn` de 18 caracteres
- **THEN** la base rechaza la escritura por exceder el largo de la columna

#### Scenario: ISBN-13 con guiones aceptado
- **WHEN** se guarda un libro con `isbn = '978-950-00-0006-6'` (17 caracteres) y el resto de datos válidos
- **THEN** la base acepta la escritura

## ADDED Requirements

### Requirement: Marca de baja lógica del libro
La tabla `libro` SHALL tener la columna `borrado_en`, `timestamptz` y nula. Un libro sin `borrado_en` es vigente; uno con fecha está dado de baja y su fila se conserva, de modo que las ventas que lo referencian siguen siendo válidas.

#### Scenario: Libro nuevo vigente
- **WHEN** se guarda un libro sin indicar `borrado_en`
- **THEN** queda con `borrado_en` nulo

#### Scenario: Columna con zona horaria
- **WHEN** se inspecciona el DDL de `libro`
- **THEN** `borrado_en` es `timestamp with time zone` y admite nulo

#### Scenario: Libros existentes al migrar
- **WHEN** se aplica la migración sobre una base con libros cargados
- **THEN** todos quedan con `borrado_en` nulo y conservan sus demás datos
