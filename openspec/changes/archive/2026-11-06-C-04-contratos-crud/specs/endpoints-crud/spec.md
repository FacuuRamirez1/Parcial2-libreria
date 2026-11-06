# Spec Delta

## Purpose

Define los endpoints CRUD por recurso: POST (201), GET lista paginada, GET {id} (200/404), PATCH {id} (200, `exclude_unset`, excepto ventas), DELETE /libros/{id} (204, soft delete) y la búsqueda del catálogo de libros.

## ADDED Requirements

### Requirement: POST por recurso responde 201

Cada recurso (`/editoriales/`, `/generos/`, `/autores/`, `/libros/`, `/clientes/`, `/ventas/`) SHALL aceptar `POST /` y responder 201 con el DTO de lectura creado.

#### Scenario: Alta de editorial

- **WHEN** se envía `POST /editoriales/` con un cuerpo válido
- **THEN** la API responde 201 con el `EditorialRead` creado

### Requirement: GET lista paginada

Cada recurso SHALL aceptar `GET /` con los parámetros `page` y `size`, respondiendo `PaginatedResponse[Read]`.

#### Scenario: Listado paginado

- **WHEN** se envía `GET /editoriales/?page=1&size=20`
- **THEN** la API responde 200 con `items`, `total`, `page`, `size` y `pages`

### Requirement: GET {id} responde 200 o 404

Cada recurso SHALL aceptar `GET /{id}`; MUST responder 200 con el DTO si existe y 404 con mensaje propio si no existe.

#### Scenario: Recurso inexistente

- **WHEN** se envía `GET /editoriales/999999`
- **THEN** la API responde 404 con un mensaje propio, sin texto interno de la base

### Requirement: PATCH {id} responde 200 excepto ventas

Cada recurso excepto `ventas` SHALL aceptar `PATCH /{id}` aplicando `exclude_unset`; MUST responder 200 con el DTO actualizado.

#### Scenario: Actualización parcial de género

- **WHEN** se envía `PATCH /generos/{id}` con solo `nombre`
- **THEN** la API responde 200 con el nombre actualizado y el resto de los campos sin cambios

### Requirement: Sin PATCH de ventas

El módulo `ventas` MUST NOT exponer `PATCH /ventas/{id}`.

#### Scenario: PATCH a ventas rechazado

- **WHEN** se envía `PATCH /ventas/1`
- **THEN** la API responde 405

### Requirement: DELETE /libros/{id} responde 204 con soft delete

`DELETE /libros/{id}` SHALL establecer `borrado_en` (soft delete) y responder 204; MUST NOT borrar físicamente la fila.

#### Scenario: Baja lógica de libro

- **WHEN** se envía `DELETE /libros/{id}` de un libro existente
- **THEN** la API responde 204
- **AND** un `GET /libros/{id}` posterior responde 404
- **AND** la fila sigue existiendo con `borrado_en` distinto de `null`

### Requirement: 409 ante IntegrityError

`POST` y `PATCH` que violen UNIQUE (`nombre`, `email`, `isbn`) o FK (`editorial_id`, `genero_id`, `cliente_id`, `libro_id`, `usuario_id`) SHALL responder 409 con un mensaje propio, sin texto de la base.

#### Scenario: Editorial duplicada

- **WHEN** se envía `POST /editoriales/` con un `nombre` ya existente
- **THEN** la API responde 409 con `{"detail": "Conflicto de integridad: registro duplicado o referencia inválida"}`

### Requirement: 422 ante paginación fuera de rango

`GET /` con `page > pages` y `total > 0` SHALL responder 422.

#### Scenario: Página inexistente

- **WHEN** se envía `GET /libros/?page=999999&size=20` habiendo libros
- **THEN** la API responde 422 con el detalle `"Página fuera de rango"`

### Requirement: Búsqueda de libros por título y género

`GET /libros/` SHALL aceptar los filtros opcionales `titulo` (búsqueda parcial case-insensitive) y `genero_id` (coincidencia exacta), combinables entre sí y con la paginación. El patrón de búsqueda MUST viajar como parámetro ligado y MUST NOT concatenarse en el SQL.

#### Scenario: Búsqueda case-insensitive

- **WHEN** existen los libros `"Cien años de soledad"` y `"Rayuela"` y se envía `GET /libros/?titulo=CIEN AÑOS`
- **THEN** la respuesta 200 tiene `total = 1` e `items` solo con `"Cien años de soledad"`

#### Scenario: Intento de inyección

- **WHEN** se envía `GET /libros/?titulo=' OR 1=1 --`
- **THEN** la respuesta 200 tiene `total = 0` e `items = []`, sin error de SQL

#### Scenario: Filtro por género

- **WHEN** existen libros de dos géneros y se envía `GET /libros/?genero_id={id}`
- **THEN** la respuesta 200 solo incluye libros de ese género

#### Scenario: Búsqueda sin coincidencias

- **WHEN** se envía `GET /libros/?titulo=inexistente`
- **THEN** la respuesta 200 tiene `total = 0`, `items = []` y `pages = 1`
