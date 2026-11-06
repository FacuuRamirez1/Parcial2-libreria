# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo editoriales, separados de la tabla `editorial`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: EditorialCreate
DTO de entrada para crear una editorial. Campos: `nombre` (str, max_length=120), `pais` (str, max_length=60). `ConfigDict(extra="forbid")`.

#### Scenario: Campo extra rechazado
- **WHEN** se envía `POST /editoriales/` con un campo que no está en `EditorialCreate`
- **THEN** la API responde 422 (`extra="forbid"`)

### Requirement: EditorialUpdate
DTO de entrada para actualizar una editorial. Todos los campos opcionales. `ConfigDict(extra="forbid")`.

### Requirement: EditorialRead
DTO de salida. Campos: `id` (int), `nombre` (str), `pais` (str).
