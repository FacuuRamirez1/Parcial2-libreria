# Spec Delta

## Purpose

Define los endpoints CRUD por recurso: POST (201), GET lista paginada, GET {id} (200/404), PATCH {id} (200, exclude_unset, excepto ventas), DELETE /libros/{id} (204, soft delete).

## ADDED Requirements

### Requirement: POST por recurso → 201
Cada recurso (`/editoriales`, `/generos`, `/autores`, `/libros`, `/clientes`, `/ventas`) acepta `POST /` y responde 201 con el DTO de lectura creado.

### Requirement: GET lista paginada
Cada recurso acepta `GET /` con parámetros `page` y `size`, respondiendo `PaginatedResponse[Read]`.

### Requirement: GET {id} → 200 / 404
Cada recurso acepta `GET /{id}`; responde 200 con el DTO si existe, 404 con mensaje propio si no.

### Requirement: PATCH {id} → 200 (excepto ventas)
Cada recurso excepto `ventas` acepta `PATCH /{id}` con `exclude_unset`; responde 200 con el DTO actualizado.

### Requirement: Sin PATCH de ventas
El módulo `ventas` **no** expone `PATCH /{id}`.

### Requirement: DELETE /libros/{id} → 204 soft delete
`DELETE /libros/{id}` establece `borrado_en` (soft delete) y responde 204; no borra físicamente la fila.

### Requirement: 409 ante IntegrityError
`POST`/`PATCH` que violen UNIQUE (nombre, email, isbn) o FK (editorial_id, genero_id, cliente_id, libro_id) responden 409 con mensaje propio (sin texto de la base).

### Requirement: 422 ante paginación fuera de rango
`GET /` con `page > pages` (y `total > 0`) responde 422.
