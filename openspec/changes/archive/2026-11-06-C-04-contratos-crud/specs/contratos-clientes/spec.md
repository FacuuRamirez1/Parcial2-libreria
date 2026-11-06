# Spec Delta

## Purpose

Define los DTOs de entrada y salida del módulo clientes (incluido perfil de cliente), separados de las tablas `cliente` y `perfil_cliente`, con validación estricta de entrada (`extra="forbid"`).

## ADDED Requirements

### Requirement: ClienteCreate

El DTO de entrada `ClienteCreate` SHALL declarar `nombre` (str, `max_length=120`) y `email` (str, `max_length=254`) obligatorios, y `usuario_id` (int | None) opcional, con `ConfigDict(extra="forbid")`.

#### Scenario: Alta válida sin usuario

- **WHEN** se envía `POST /clientes/` con `nombre` y `email`
- **THEN** la API responde 201 con `usuario_id = null`

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /clientes/` con un campo no declarado
- **THEN** la API responde 422

### Requirement: ClienteUpdate

El DTO de entrada `ClienteUpdate` SHALL permitir `nombre`, `email` y `usuario_id` opcionales y MUST rechazar campos no declarados con `ConfigDict(extra="forbid")`.

#### Scenario: Actualización parcial

- **WHEN** se envía `PATCH /clientes/{id}` con solo `nombre`
- **THEN** la API responde 200 y conserva `email` y `usuario_id`

### Requirement: ClienteRead

El DTO de salida `ClienteRead` SHALL exponer `id` (int), `nombre` (str), `email` (str) y `usuario_id` (int | None).

#### Scenario: Representación de salida

- **WHEN** se consulta `GET /clientes/{id}` de un cliente existente
- **THEN** el cuerpo contiene `id`, `nombre`, `email` y `usuario_id`

### Requirement: PerfilClienteCreate

El DTO de entrada `PerfilClienteCreate` SHALL declarar `telefono` (str, `max_length=30`) y `direccion` (str, `max_length=255`) obligatorios, y `cliente_id` (int | None) opcional. El `id` de la ruta `POST /clientes/{id}/perfil` SHALL ser autoritativo: si el cuerpo incluye `cliente_id`, MUST coincidir con el de la ruta o la API responde 422.

#### Scenario: Alta sin cliente_id en el cuerpo

- **WHEN** se envía `POST /clientes/{id}/perfil` sin `cliente_id`
- **THEN** la API responde 201 y asocia el perfil al cliente de la ruta

#### Scenario: cliente_id inconsistente

- **WHEN** se envía `POST /clientes/{id}/perfil` con un `cliente_id` distinto del de la ruta
- **THEN** la API responde 422

#### Scenario: Campo extra rechazado

- **WHEN** se envía `POST /clientes/{id}/perfil` con un campo no declarado
- **THEN** la API responde 422

### Requirement: PerfilClienteRead

El DTO de salida `PerfilClienteRead` SHALL exponer `id` (int), `telefono` (str), `direccion` (str) y `cliente_id` (int).

#### Scenario: Representación de salida

- **WHEN** se crea un perfil de cliente
- **THEN** la respuesta 201 contiene `id`, `telefono`, `direccion` y `cliente_id`
