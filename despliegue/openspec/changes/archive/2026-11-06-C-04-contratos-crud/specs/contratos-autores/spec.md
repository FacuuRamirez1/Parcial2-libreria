# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo autores, separados de la tabla `autor`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: AutorCreate

El DTO de entrada `AutorCreate` SHALL declarar `nombre` (str, `max_length=120`) y `nacionalidad` (str, `max_length=60`), ambos obligatorios, con `ConfigDict(extra="forbid")`.

#### Scenario: Alta válida

- **WHEN** se envía `POST /autores/` con `nombre` y `nacionalidad`
- **THEN** la API responde 201 con el `AutorRead` creado

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /autores/` con un campo no declarado en `AutorCreate`
- **THEN** la API responde 422 por `extra="forbid"`

#### Scenario: Campo obligatorio ausente

- **WHEN** se envía `POST /autores/` sin `nacionalidad`
- **THEN** la API responde 422

### Requirement: AutorUpdate

El DTO de entrada `AutorUpdate` SHALL permitir `nombre` y `nacionalidad` opcionales y MUST rechazar campos no declarados con `ConfigDict(extra="forbid")`.

#### Scenario: Actualización parcial

- **WHEN** se envía `PATCH /autores/{id}` con solo `nombre`
- **THEN** la API responde 200 y conserva la `nacionalidad` previa

#### Scenario: Campo extra rechazado

- **WHEN** se envía `PATCH /autores/{id}` con un campo no declarado
- **THEN** la API responde 422

### Requirement: AutorRead

El DTO de salida `AutorRead` SHALL exponer `id` (int), `nombre` (str) y `nacionalidad` (str), sin campos internos.

#### Scenario: Representación de salida

- **WHEN** se consulta `GET /autores/{id}` de un autor existente
- **THEN** el cuerpo contiene exactamente `id`, `nombre` y `nacionalidad`
