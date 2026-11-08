# migraciones-esquema Specification

## Purpose
Definir cómo Alembic administra el esquema PostgreSQL de la librería: configuración asincrónica sin secretos versionados, creación completa del esquema mediante migraciones y capacidad de revertir y reaplicar la cadena sin drift.

## Requirements

### Requirement: Configuración asincrónica sin credenciales versionadas

Alembic SHALL ejecutarse con motor asincrónico y SHALL obtener la URL de `DATABASE_URL`, definida en el entorno o en un `.env` local no versionado. `alembic.ini` NO SHALL contener usuario, clave ni URL de conexión. Si falta `DATABASE_URL`, la ejecución MUST fallar con un mensaje que nombre la variable, sin incluir su valor.

#### Scenario: URL tomada del entorno

- **WHEN** se ejecuta `alembic upgrade head` con `DATABASE_URL` definida
- **THEN** Alembic se conecta con esa URL usando `async_engine_from_config`
- **AND** `alembic.ini` no contiene credenciales

#### Scenario: Falta DATABASE_URL

- **WHEN** se ejecuta Alembic sin `DATABASE_URL` en el entorno ni en `.env`
- **THEN** falla con un error que indica que falta `DATABASE_URL`
- **AND** el mensaje no expone ningún valor de conexión

### Requirement: Esquema completo creado por migraciones

Una base vacía SHALL quedar con el esquema completo al ejecutar `alembic upgrade head`. El esquema MUST contener las 9 tablas de la consigna y las 5 tablas de infraestructura de acceso/stock: `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`, `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`. La aplicación y los tests NO SHALL crear tablas con `create_all`.

#### Scenario: Base vacía migrada

- **WHEN** se ejecuta `alembic upgrade head` contra una base PostgreSQL vacía
- **THEN** existen las 14 tablas del metadata con sus restricciones e índices
- **AND** la revisión actual es `0003_drop_ix_cliente_usuario_id`

#### Scenario: Sin creación automática de esquema

- **WHEN** se busca `create_all` en `app/`, `scripts/` y `test/`
- **THEN** no existe ninguna llamada que cree tablas fuera de Alembic

### Requirement: Migraciones reversibles y sin drift

La cadena de migraciones SHALL poder revertirse y reaplicarse sin errores. El esquema migrado MUST coincidir con `SQLModel.metadata`, de modo que `alembic check` no detecte operaciones pendientes.

#### Scenario: Ciclo downgrade y upgrade

- **WHEN** se ejecuta `alembic downgrade -1` y luego `alembic upgrade head` sobre una base migrada
- **THEN** ambas operaciones terminan sin error
- **AND** el esquema vuelve a la cabeza `0003_drop_ix_cliente_usuario_id`

#### Scenario: Sin drift entre modelos y migraciones

- **WHEN** se ejecuta `alembic check` contra una base migrada
- **THEN** responde “No new upgrade operations detected”
