# unit-of-work-modulos Specification

## Purpose

Define el contrato del Unit of Work por módulo: gestor de contexto async que confirma al salir del bloque, revierte ante excepción, no crea ni cierra la sesión y compone los repositorios del módulo sobre una misma sesión.

## Requirements

### Requirement: Unit of Work como gestor de contexto async

El UoW SHALL ser usable con `async with`; confirma las escrituras al salir exitosamente del bloque y revierte si sale con excepción.

#### Scenario: Confirmación al salir del bloque

- **WHEN** se realiza al menos una escritura dentro de `async with uow:` y el bloque finaliza sin excepción
- **THEN** las escrituras se confirman (commit) en la base

#### Scenario: Reversión ante excepción

- **WHEN** se lanza una excepción dentro de `async with uow:` tras una escritura
- **THEN** las escrituras se deshacen (rollback) y la excepción se propaga

### Requirement: El UoW no crea ni cierra la sesión

El UoW SHALL recibir la sesión desde el exterior y no cerrarla ni disponerla.

#### Scenario: Sesión externa

- **WHEN** se construye el UoW pasando una sesión existente
- **THEN** el UoW usa esa sesión y no la cierra al salir del bloque (la cierra el dueño de la sesión)

### Requirement: Un repositorio por entidad con la misma sesión

El UoW de un módulo SHALL exponer el repositorio de cada entidad del módulo, todos sobre la misma sesión de la petición.

#### Scenario: Mismatch de sesión

- **WHEN** se accede a dos repositorios del mismo UoW
- **THEN** ambos operan sobre la misma sesión (una sola conexión por petición autenticada)

### Requirement: Construcción del UoW en el router y apertura en el servicio

El router SHALL construir el UoW mediante una dependencia y pasárselo sin abrir al servicio; el servicio SHALL abrirlo con `async with` y nunca construirlo.

#### Scenario: Flujo router → servicio

- **WHEN** una petición llega al router
- **THEN** el router crea el UoW por dependencia, el servicio lo abre con `async with` y el UoW confirma o revierte al salir
