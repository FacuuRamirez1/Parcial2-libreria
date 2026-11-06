# Spec Delta

## Purpose

Define el esquema del catálogo de la librería (editoriales, géneros, autores, libros y la autoría libro–autor con rol y orden) y las garantías de integridad y de largo que la propia base impone sobre esos datos.

## ADDED Requirements

### Requirement: Tabla editorial
El esquema SHALL incluir la tabla `editorial` con las columnas `id` (clave primaria entera generada por la base), `nombre` (`VARCHAR(120)`) y `pais` (`VARCHAR(60)`), ambas obligatorias. El `nombre` SHALL ser único (sustenta el 409 de `POST /editoriales/`).

#### Scenario: Columnas de editorial
- **WHEN** se inspecciona el esquema generado para `editorial`
- **THEN** existen exactamente las columnas `id`, `nombre VARCHAR(120) NOT NULL` y `pais VARCHAR(60) NOT NULL`, con `id` como clave primaria

#### Scenario: Nombre de editorial repetido
- **WHEN** se intenta guardar una segunda editorial con un `nombre` ya existente
- **THEN** la base rechaza la escritura por violación de unicidad

### Requirement: Tabla genero
El esquema SHALL incluir la tabla `genero` con las columnas `id` (clave primaria entera generada por la base) y `nombre` (`VARCHAR(60)`, obligatorio y único).

#### Scenario: Nombre de género repetido
- **WHEN** se intenta guardar un segundo género con un `nombre` ya existente
- **THEN** la base rechaza la escritura por violación de unicidad

### Requirement: Tabla autor
El esquema SHALL incluir la tabla `autor` con las columnas `id` (clave primaria entera generada por la base), `nombre` (`VARCHAR(120)`) y `nacionalidad` (`VARCHAR(60)`), ambas obligatorias, sin restricciones de unicidad.

#### Scenario: Autores homónimos permitidos
- **WHEN** se guardan dos autores con el mismo `nombre`
- **THEN** la base acepta ambos registros con `id` distintos

### Requirement: Tabla libro con ISBN único
El esquema SHALL incluir la tabla `libro` con las columnas `id`, `isbn`, `titulo`, `precio`, `stock`, `editorial_id` y `genero_id`. `isbn` SHALL ser `VARCHAR(17)` obligatorio (ISBN-13 con guiones) y `titulo` `VARCHAR(255)` obligatorio; `stock` entero obligatorio. El `isbn` SHALL ser único (RN-01).

#### Scenario: ISBN repetido
- **WHEN** se intenta guardar un libro con un `isbn` que ya tiene otro libro
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Tipo de las columnas de texto de libro
- **WHEN** se inspecciona el DDL de `libro` para PostgreSQL
- **THEN** `isbn` es `VARCHAR(17) NOT NULL` y `titulo` es `VARCHAR(255) NOT NULL`

#### Scenario: ISBN más largo que la columna
- **WHEN** se intenta guardar directamente en la base un libro con un `isbn` de 18 caracteres
- **THEN** la base rechaza la escritura por exceder el largo de la columna

#### Scenario: ISBN-13 con guiones aceptado
- **WHEN** se guarda un libro con `isbn = '978-950-00-0006-6'` (17 caracteres) y el resto de datos válidos
- **THEN** la base acepta la escritura

### Requirement: Precio del libro exacto y positivo
La columna `libro.precio` SHALL ser decimal exacto `NUMERIC(10,2)` (nunca coma flotante) y la base SHALL rechazar valores menores o iguales a cero (RN-03).

#### Scenario: Tipo de la columna precio
- **WHEN** se inspecciona el DDL de `libro` para PostgreSQL
- **THEN** `precio` es `NUMERIC(10, 2) NOT NULL`

#### Scenario: Precio cero rechazado
- **WHEN** se intenta guardar un libro con `precio = 0`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

### Requirement: Stock del libro no negativo
La base SHALL rechazar un `libro.stock` negativo y SHALL aceptar `stock = 0` (RN-03).

#### Scenario: Stock negativo rechazado
- **WHEN** se intenta guardar un libro con `stock = -1`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

#### Scenario: Stock cero aceptado
- **WHEN** se guarda un libro con `stock = 0` y el resto de datos válidos
- **THEN** la base acepta la escritura

### Requirement: Libro pertenece a una editorial existente
`libro.editorial_id` SHALL ser obligatorio y clave foránea a `editorial.id`, con un índice propio. La base SHALL rechazar un libro cuya editorial no existe (sin consulta previa en la aplicación).

#### Scenario: Editorial inexistente
- **WHEN** se intenta guardar un libro con `editorial_id` que no corresponde a ninguna editorial
- **THEN** la base rechaza la escritura por violación de clave foránea

### Requirement: Género opcional del libro
`libro.genero_id` SHALL admitir NULL y, cuando tiene valor, SHALL ser clave foránea a `genero.id`, con un índice propio. Esta columna, su FK, su índice y la tabla `genero` SHALL poder separarse del resto del esquema sin afectar a las demás tablas (lo requiere la 2ª migración de C-03).

#### Scenario: Libro sin género
- **WHEN** se guarda un libro con `genero_id` nulo y el resto de datos válidos
- **THEN** la base acepta la escritura

#### Scenario: Género inexistente
- **WHEN** se intenta guardar un libro con un `genero_id` que no corresponde a ningún género
- **THEN** la base rechaza la escritura por violación de clave foránea

### Requirement: Autoría libro–autor como entidad con rol y orden
El esquema SHALL incluir la tabla `libro_autor` con las columnas `libro_id` (FK a `libro.id`), `autor_id` (FK a `autor.id`, con índice propio), `rol` (`VARCHAR(20)` obligatorio) y `orden` (entero obligatorio), con clave primaria compuesta (`libro_id`, `autor_id`).

#### Scenario: Mismo autor dos veces en un libro
- **WHEN** se intenta guardar dos filas de `libro_autor` con el mismo par (`libro_id`, `autor_id`)
- **THEN** la base rechaza la escritura por violación de clave primaria

#### Scenario: Tipo de la columna rol
- **WHEN** se inspecciona el DDL de `libro_autor` para PostgreSQL
- **THEN** `rol` es `VARCHAR(20) NOT NULL` y `orden` es `INTEGER NOT NULL`

#### Scenario: Autor inexistente en la autoría
- **WHEN** se intenta guardar una fila de `libro_autor` con un `autor_id` inexistente
- **THEN** la base rechaza la escritura por violación de clave foránea

### Requirement: Valores válidos de rol y orden
La base SHALL rechazar en `libro_autor` un `rol` distinto de `autor`, `coautor`, `traductor` o `ilustrador`, y un `orden` menor que 1.

#### Scenario: Rol fuera de la lista
- **WHEN** se intenta guardar una autoría con `rol = 'editor'`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

#### Scenario: Orden cero
- **WHEN** se intenta guardar una autoría con `orden = 0`
- **THEN** la base rechaza la escritura por violación de una restricción CHECK

### Requirement: Navegación del catálogo en ambos extremos
Cada relación del catálogo SHALL navegarse desde los dos extremos: un libro expone su editorial, su género (o ninguno) y sus autorías; una editorial y un género exponen sus libros; un autor expone sus autorías; cada autoría expone su libro y su autor. Las autorías de un libro SHALL entregarse ordenadas por `orden`.

#### Scenario: Autores de un libro con rol y orden
- **WHEN** se lee un libro con sus autorías precargadas
- **THEN** cada autoría da acceso a su `rol`, su `orden` y su autor, y la lista está ordenada por `orden` ascendente

#### Scenario: Libros de una editorial
- **WHEN** se lee una editorial con sus libros precargados
- **THEN** la editorial da acceso a la colección de sus libros, y cada libro a la misma editorial
