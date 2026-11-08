# Spec Delta

## Purpose

Define el contrato del repositorio de la entidad Libro: obtención por id, listado paginado con precarga de editorial y género, búsqueda filtrada por título y género, conteo total y filtrado, y escritura mediante flush, sin carga perezosa y sin borrado lógico en esta fase.

## ADDED Requirements

### Requirement: Obtención de libro por id con precarga

El repositorio SHALL devolver el libro solicitado por su id con editorial y género precargados, o nulo si no existe.

#### Scenario: Libro existente

- **WHEN** se consulta el repositorio por un id de libro presente
- **THEN** devuelve la entidad Libro con editorial y género ya cargados (sin consultas adicionales)

#### Scenario: Libro inexistente

- **WHEN** se consulta el repositorio por un id de libro ausente
- **THEN** devuelve nulo sin lanzar excepción

### Requirement: Listado paginado de libros con precarga

El repositorio SHALL listar libros aplicando `offset`/`limit`, orden estable por id, y precargando editorial y género con `joinedload`.

#### Scenario: Listado paginado de libros

- **WHEN** se solicita `get_all` con `offset` y `limit`
- **THEN** devuelve hasta `limit` libros con editorial y género precargados, ordenados por id

### Requirement: Búsqueda filtrada de libros

El repositorio SHALL filtrar libros por título (coincidencia parcial, sin distinguir mayúsculas, parámetro ligado) y por `genero_id` opcional, respetando la paginación.

#### Scenario: Búsqueda por título y género

- **WHEN** se invoca `get_all_filtrado` con `titulo` y `genero_id`
- **THEN** devuelve libros cuyo título contenga el texto (case-insensitive, parámetro ligado) y cuyo género coincida, aplicando `offset`/`limit`

### Requirement: Conteo de libros total y filtrado

El repositorio SHALL devolver la cantidad total de libros y la cantidad que cumple un filtro dado.

#### Scenario: Conteo total

- **WHEN** se invoca `count`
- **THEN** devuelve la cantidad de filas de la tabla libro

#### Scenario: Conteo filtrado

- **WHEN** se invoca `count_filtrado` con los mismos filtros de un listado
- **THEN** devuelve la cantidad de filas que cumplen esos filtros

### Requirement: Escritura de libro mediante flush

El repositorio SHALL agregar, actualizar o eliminar un libro con `flush()` y nunca con `commit()`. El stock no se edita por PATCH en esta fase.

#### Scenario: Alta de libro

- **WHEN** se invoca `add` con una entidad Libro y se hace flush
- **THEN** el libro persiste en la transacción abierta sin confirmarla

### Requirement: Ausencia de borrado lógico de libro en esta fase

El repositorio SHALL no aplicar filtro `borrado_en IS NULL` ni exponer `soft_delete`, porque `libro.borrado_en` no existe hasta C-10.

#### Scenario: No filtro de borrado

- **WHEN** se listan libros en C-09
- **THEN** no se aplica filtro de `borrado_en` (la columna no existe)
