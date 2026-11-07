# Spec Delta

## Purpose

Define el gestor de contexto asincrónico que agrupa varias escrituras en una sola transacción: confirma al salir del bloque, revierte ante excepción y no cierra la sesión porque no la creó.

## ADDED Requirements

### Requirement: UnitOfWork como gestor de contexto asincrónico
`UnitOfWork` SHALL ser un gestor de contexto asincrónico que se abre con `async with` y que confirma al salir del bloque sin excepción y revierte si se sale con una excepción.

#### Confirmación al salir sin excepción
- **WHEN** un bloque `async with unit_of_work:` finaliza sin lanzar excepción
- **THEN** se confirma la transacción (`commit`)

#### Reversión ante excepción
- **WHEN** un bloque `async with unit_of_work:` sale lanzando una excepción
- **THEN** se revierte la transacción (`rollback`)

### Requirement: No cierra la sesión
El `UnitOfWork` SHALL no cerrar la sesión de base de datos, porque no la creó; quien creó la sesión (`get_session`) es la responsable de cerrarla.

#### Sesión persistente tras el UoW
- **WHEN** se sale de un bloque `async with unit_of_work:`
- **THEN** la sesión subyacente no se cierra

### Requirement: Repositorios sobre la misma sesión
Un `UnitOfWork` por módulo SHALL componer los repositorios que sus operaciones necesitan, todos sobre la misma sesión de base de datos.

#### Mismo sesión en los repositorios del UoW
- **WHEN** un `UnitOfWork` de un módulo expone varios repositorios
- **THEN** todos usan la misma sesión de base de datos

### Requirement: El router construye, el servicio abre
El router SHALL construir el `UnitOfWork` con una dependencia y pasarlo al servicio sin abrirlo; el servicio SHALL abrirlo con `async with` y NUNCA construir su propio `UnitOfWork`.

#### Router pasa el UoW sin abrir
- **WHEN** el router construye el `UnitOfWork` y lo envía al servicio
- **THEN** el servicio lo recibe sin haber entrado al bloque `async with`

#### Servicio abre con async with
- **WHEN** el servicio necesita agrupar escrituras
- **THEN** abre el `UnitOfWork` con `async with` y nunca lo construye él mismo
