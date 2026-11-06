# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo géneros, separados de la tabla `genero`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: GeneroCreate
DTO de entrada para crear un género. Campo: `nombre` (str, max_length=60). `ConfigDict(extra="forbid")`.

### Requirement: GeneroUpdate
DTO de entrada para actualizar un género. Campo opcional: `nombre`. `ConfigDict(extra="forbid")`.

### Requirement: GeneroRead
DTO de salida. Campos: `id` (int), `nombre` (str).
