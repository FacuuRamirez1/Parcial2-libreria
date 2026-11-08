# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo géneros, separados de la tabla `genero`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: GeneroCreate

El DTO de entrada `GeneroCreate` SHALL declarar `nombre` (str, `max_length=60`) obligatorio, con `ConfigDict(extra="forbid")`.

#### Scenario: Alta válida

- **WHEN** se envía `POST /generos/` con `nombre`
- **THEN** la API responde 201 con el `GeneroRead` creado

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /generos/` con un campo no declarado
- **THEN** la API responde 422

### Requirement: GeneroUpdate

El DTO de entrada `GeneroUpdate` SHALL permitir `nombre` opcional y MUST rechazar campos no declarados con `ConfigDict(extra="forbid")`.

#### Scenario: Actualización parcial

- **WHEN** se envía `PATCH /generos/{id}` con `nombre`
- **THEN** la API responde 200 con el nombre actualizado

#### Scenario: Campo extra rechazado

- **WHEN** se envía `PATCH /generos/{id}` con un campo no declarado
- **THEN** la API responde 422

### Requirement: GeneroRead

El DTO de salida `GeneroRead` SHALL exponer `id` (int) y `nombre` (str).

#### Scenario: Representación de salida

- **WHEN** se consulta `GET /generos/{id}` de un género existente
- **THEN** el cuerpo contiene `id` y `nombre`
