# repositorios-libros Specification

## Purpose

Define el contrato del repositorio de la entidad Libro: obtención por id, listado paginado con precarga de editorial y género, búsqueda filtrada por título y género, conteo total y filtrado, y escritura mediante flush, sin carga perezosa y sin borrado lógico en esta fase.

## Requirements

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
El repositorio SHALL agregar, actualizar o eliminar (baja lógica) un libro con `flush()` y nunca con `commit()`. El stock NO SHALL editarse por PATCH ni por una escritura directa del repositorio: solo cambia por el punto único de escritura de stock.

#### Scenario: Alta de libro
- **WHEN** se invoca `add` con una entidad Libro y se hace flush
- **THEN** el libro persiste en la transacción abierta sin confirmarla

#### Scenario: Baja lógica
- **WHEN** se invoca `soft_delete` con un libro vigente
- **THEN** el libro queda con `borrado_en` no nulo y persiste sin confirmar

### Requirement: Lecturas del repositorio con baja lógica
`get_by_id`, `get_all`, `get_all_filtrado` y `count_filtrado` SHALL excluir los libros con `borrado_en` no nulo. El repositorio SHALL ofrecer `get_by_id_including_deleted` para lecturas internas que necesiten un libro dado de baja.

#### Scenario: Listado sin dados de baja
- **WHEN** se invoca `get_all_filtrado` después de dar de baja un libro
- **THEN** el libro dado de baja no aparece en el resultado

#### Scenario: Acceso incluyendo dados de baja
- **WHEN** se invoca `get_by_id_including_deleted` con el id de un libro dado de baja
- **THEN** devuelve la entidad

### Requirement: Historial de movimientos de un libro
El repositorio de libros SHALL ofrecer un método para listar los movimientos de un libro ordenados por id, sin carga perezosa, para `GET /libros/{id}/movimientos`.

#### Scenario: Movimientos ordenados
- **WHEN** se listan los movimientos de un libro con alta, reposición y venta
- **THEN** devuelve las tres filas ordenadas por id ascendente
