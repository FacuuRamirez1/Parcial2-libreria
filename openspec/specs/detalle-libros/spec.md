# detalle-libros Specification

## Purpose
Define el detalle de libro con editorial, género y autores precargados, tanto en `GET /libros/{id}` como en el listado, sin carga perezosa y con un número fijo de consultas.

## Requirements

### Requirement: DTO LibroDetalleRead

`LibroDetalleRead` SHALL extender `LibroRead` agregando `editorial` (`EditorialRead`), `genero` (`GeneroRead | None`) y `autores` (`list[LibroAutorRead]`), donde `LibroAutorRead` expone `autor` (`AutorRead`), `rol` y `orden`. Los campos planos de `LibroRead` MUST conservarse sin cambios.

#### Scenario: Detalle con editorial, género y autores

- **WHEN** se consulta `GET /libros/{id}` de un libro con editorial, género y dos autores
- **THEN** la respuesta 200 incluye `editorial.nombre`, `genero.nombre` y `autores` con `autor.nombre`, `rol` y `orden` de cada autoría

#### Scenario: Libro sin género

- **WHEN** se consulta `GET /libros/{id}` de un libro con `genero_id = null`
- **THEN** la respuesta 200 incluye `genero: null` y no falla

#### Scenario: Libro sin autores

- **WHEN** se consulta `GET /libros/{id}` de un libro sin autorías
- **THEN** la respuesta 200 incluye `autores: []`

### Requirement: Precarga de detalle en GET /libros/{id}

`GET /libros/{id}` SHALL cargar el libro, su editorial y su género con `joinedload`, y sus autorías con su autor con `selectinload`, declarados en la misma operación de consulta. La respuesta MUST NOT depender de carga perezosa.

#### Scenario: Detalle con relaciones precargadas

- **WHEN** el repositorio obtiene un libro con `get_by_id_con_detalle(id)`
- **THEN** las relaciones `editorial`, `genero` y `autorias → autor` quedan cargadas y acceder a ellas no emite consultas adicionales

### Requirement: Listado de libros con detalle precargado

`GET /libros/` SHALL responder `PaginatedResponse[LibroDetalleRead]` y MUST aplicar las mismas opciones de precarga a cada elemento de la página.

#### Scenario: Listado con detalle

- **WHEN** se consulta `GET /libros/?page=1&size=20` con libros que tienen autores
- **THEN** cada `item` 200 incluye `editorial`, `genero` y `autores` ya precargados

### Requirement: Conteo fijo de consultas en libros

El número de sentencias `SELECT` ejecutadas por `GET /libros/{id}` SHALL ser 2, independientemente de la cantidad de autores (0, 1 o N). El número para `GET /libros/` SHALL ser 3 (conteo, página y autorías), independientemente de la cantidad de libros y autores.

#### Scenario: Detalle con 1 vs. 3 autores

- **WHEN** se mide `GET /libros/{id}` para un libro con 1 autor y para otro con 3 autores
- **THEN** ambos requests ejecutan exactamente 2 `SELECT`

#### Scenario: Listado con distinta cantidad de libros

- **WHEN** se mide `GET /libros/` con 1 libro y con varios libros que tienen autores
- **THEN** ambos requests ejecutan exactamente 3 `SELECT`
