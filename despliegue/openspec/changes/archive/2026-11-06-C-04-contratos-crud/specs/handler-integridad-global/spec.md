# Spec Delta

## Purpose

Define el handler global de errores que traduce `IntegrityError` (y `DataError` como red de seguridad) a respuestas HTTP con mensajes propios, sin texto interno de la base de datos (RN-12).

## ADDED Requirements

### Requirement: Handler global de IntegrityError responde 409

El sistema SHALL registrar un exception handler para `sqlalchemy.exc.IntegrityError` que responda HTTP 409 con un mensaje propio y limpio.

#### Scenario: Duplicado de UNIQUE

- **WHEN** se envía `POST /editoriales/` con un `nombre` ya existente
- **THEN** la base rechaza por `uq_editorial_nombre`; el handler captura `IntegrityError` y responde 409 `{"detail": "Conflicto de integridad: registro duplicado o referencia inválida"}` sin el nombre de la restricción ni el mensaje del driver

#### Scenario: FK inválida

- **WHEN** se envía `POST /libros/` con `editorial_id` inexistente
- **THEN** la base rechaza por `fk_libro_editorial_id_editorial` y el handler responde 409 con el mensaje propio

### Requirement: Handler de DataError responde 422

El sistema SHALL registrar un exception handler para `sqlalchemy.exc.DataError` que responda HTTP 422 con un mensaje propio cuando un valor excede el tamaño de una columna `VARCHAR(n)`.

#### Scenario: Texto demasiado largo

- **WHEN** se envía un `isbn` de 18 caracteres (columna `VARCHAR(17)`)
- **THEN** el handler captura `DataError` y responde 422 con el mensaje propio, sin texto de la base

### Requirement: Nunca texto interno de la base

Ninguna respuesta de error MUST incluir nombres de tablas, restricciones, columnas, mensajes del driver ni trazas de SQLAlchemy.

#### Scenario: Respuesta de error saneada

- **WHEN** se provoca un `IntegrityError` o un `DataError`
- **THEN** el cuerpo de la respuesta no contiene `uq_`, `fk_`, `INSERT`, `UPDATE`, `psycopg` ni `asyncpg`
