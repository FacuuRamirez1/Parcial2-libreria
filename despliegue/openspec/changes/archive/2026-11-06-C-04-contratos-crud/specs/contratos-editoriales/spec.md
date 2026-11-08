# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo editoriales, separados de la tabla `editorial`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: EditorialCreate

El DTO de entrada `EditorialCreate` SHALL declarar `nombre` (str, `max_length=120`) y `pais` (str, `max_length=60`) obligatorios, con `ConfigDict(extra="forbid")`.

#### Scenario: Alta válida

- **WHEN** se envía `POST /editoriales/` con `nombre` y `pais`
- **THEN** la API responde 201 con el `EditorialRead` creado

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /editoriales/` con un campo que no está en `EditorialCreate`
- **THEN** la API responde 422 (`extra="forbid"`)

### Requirement: EditorialUpdate

El DTO de entrada `EditorialUpdate` SHALL permitir `nombre` y `pais` opcionales y MUST rechazar campos no declarados con `ConfigDict(extra="forbid")`.

#### Scenario: Actualización parcial

- **WHEN** se envía `PATCH /editoriales/{id}` con solo `nombre`
- **THEN** la API responde 200 y conserva `pais`

#### Scenario: Campo extra rechazado

- **WHEN** se envía `PATCH /editoriales/{id}` con un campo no declarado
- **THEN** la API responde 422

### Requirement: EditorialRead

El DTO de salida `EditorialRead` SHALL exponer `id` (int), `nombre` (str) y `pais` (str).

#### Scenario: Representación de salida

- **WHEN** se consulta `GET /editoriales/{id}` de una editorial existente
- **THEN** el cuerpo contiene `id`, `nombre` y `pais`
