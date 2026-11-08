# Proposal: C-06 — Lecturas sin N+1

## Why

La consigna (US-009) pide ver el detalle de un libro (editorial, género y autores) y de una venta (cliente y renglones) sin caer en N+1. Hoy `GET /libros/{id}` devuelve solo los campos planos de `LibroRead` y no precarga relaciones; las relaciones están declaradas con `lazy="raise"`, de modo que cualquier intento de exponer el detalle fallaría o dispararía consultas por fila. Las lecturas de ventas ya precargan relaciones desde C-05, pero no existe evidencia automatizada de que el número de consultas sea fijo.

## What Changes

- Nuevo DTO `LibroDetalleRead` (extiende `LibroRead`) con `editorial`, `genero` (nullable) y `autores` (`rol`, `orden`, datos del autor).
- `LibroRepository` precarga `editorial`/`genero` con `joinedload` y `autorias → autor` con `selectinload`; nuevo `get_by_id_con_detalle`.
- `GET /libros/{id}` y `GET /libros/` responden con el detalle precargado.
- Tests de conteo de sentencias SQL con 1 vs. 3 autores y 1 vs. 3 renglones, usando `before_cursor_execute`.
- Sin cambios de esquema ni migraciones: las relaciones y los índices ya existen.

## Impact

- Código: `app/modules/libros/{schemas,repository,service,router}.py`, tests nuevos.
- Contrato: se agregan campos anidados a la lectura de libros (aditivo); no se quitan campos existentes.
- Riesgo: bajo/medio. La respuesta se agranda en listados; el conteo de consultas se mantiene fijo.
