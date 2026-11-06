# Spec Delta

## Purpose

Define el componente de paginación estándar reutilizable por todos los listados de la API (`PaginatedResponse[T]`, validación de `page`/`size`, cálculo de `pages` y el error 422 cuando la página solicitada excede el total de páginas).

## ADDED Requirements

### Requirement: Modelo genérico PaginatedResponse[T]

El esquema SHALL incluir un modelo Pydantic genérico `PaginatedResponse[T]` con exactamente los campos: `items: list[T]`, `total: int`, `page: int`, `size: int` y `pages: int`.

#### Scenario: Campos exactos de PaginatedResponse

- **WHEN** se inspecciona el modelo `PaginatedResponse[EditorialRead]`
- **THEN** tiene exactamente los campos `items` (lista), `total` (int), `page` (int), `size` (int) y `pages` (int), sin campos adicionales

### Requirement: Validación de page y size

`page` SHALL ser `>= 1` con valor por defecto 1; `size` SHALL estar entre 1 y 100 con valor por defecto 20.

#### Scenario: page menor a 1

- **WHEN** se solicita `GET /editoriales/?page=0`
- **THEN** la API responde 422 por la validación de FastAPI

#### Scenario: size fuera de rango

- **WHEN** se solicita `GET /editoriales/?size=101` o `GET /editoriales/?size=0`
- **THEN** la API responde 422

#### Scenario: Valores por defecto

- **WHEN** se solicita `GET /editoriales/` sin `page` ni `size`
- **THEN** la respuesta usa `page = 1` y `size = 20`

### Requirement: Cálculo de páginas cuando total es cero

Cuando `total == 0`, `pages` SHALL ser `1` e `items` SHALL ser `[]`.

#### Scenario: Catálogo vacío

- **WHEN** se lista un recurso sin registros (`total = 0`)
- **THEN** `pages = 1`, `items = []`, `total = 0` y se respeta el `page`/`size` solicitado

### Requirement: Cálculo de páginas cuando total es mayor a cero

Cuando `total > 0`, `pages` SHALL ser `ceil(total / size)`.

#### Scenario: División exacta

- **WHEN** `total = 20` y `size = 10`
- **THEN** `pages = 2`

#### Scenario: División inexacta

- **WHEN** `total = 25` y `size = 10`
- **THEN** `pages = 3`

### Requirement: Página fuera de rango responde 422

Cuando `total > 0` y se pide `page > pages`, el sistema SHALL lanzar `HTTPException 422`.

#### Scenario: Página inexistente

- **WHEN** hay 1 registro, `size = 1` (`pages = 1`) y se pide `page = 2`
- **THEN** la API responde 422 con el mensaje propio `"Página fuera de rango"`, sin texto interno de la base

### Requirement: Función calcular_paginas

SHALL existir una función `calcular_paginas(total: int, size: int) -> int` que devuelva 1 si `total == 0` y `ceil(total / size)` en caso contrario.

#### Scenario: Total cero

- **WHEN** se llama `calcular_paginas(0, 20)`
- **THEN** devuelve `1`

#### Scenario: Total mayor a cero

- **WHEN** se llama `calcular_paginas(25, 10)`
- **THEN** devuelve `3`
