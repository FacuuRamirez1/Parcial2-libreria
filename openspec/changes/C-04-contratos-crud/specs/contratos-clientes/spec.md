# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo clientes (incluido perfil de cliente), separados de las tablas `cliente` y `perfil_cliente`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: ClienteCreate
DTO de entrada para crear un cliente. Campos: `nombre` (str, max_length=120), `email` (str, max_length=254), `usuario_id` (int | None, opcional). `ConfigDict(extra="forbid")`.

### Requirement: ClienteUpdate
DTO de entrada para actualizar un cliente. Campos opcionales: `nombre`, `email`, `usuario_id`. `ConfigDict(extra="forbid")`.

### Requirement: ClienteRead
DTO de salida. Campos: `id` (int), `nombre` (str), `email` (str), `usuario_id` (int | None).

### Requirement: PerfilClienteCreate
DTO de entrada para crear un perfil de cliente. Campos: `telefono` (str, max_length=30), `direccion` (str, max_length=255), `cliente_id` (int). `ConfigDict(extra="forbid")`.

### Requirement: PerfilClienteRead
DTO de salida. Campos: `id` (int), `telefono` (str), `direccion` (str), `cliente_id` (int).
