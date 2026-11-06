# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo autores, separados de la tabla `autor`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: AutorCreate
DTO de entrada para crear un autor. Campos: `nombre` (str, max_length=120), `nacionalidad` (str, max_length=60). `ConfigDict(extra="forbid")`.

### Requirement: AutorUpdate
DTO de entrada para actualizar un autor. Campos opcionales: `nombre`, `nacionalidad`. `ConfigDict(extra="forbid")`.

### Requirement: AutorRead
DTO de salida. Campos: `id` (int), `nombre` (str), `nacionalidad` (str).
