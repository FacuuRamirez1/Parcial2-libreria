# migraciones-esquema Specification

## Purpose
Definir cómo Alembic administra el esquema PostgreSQL de la librería: configuración asincrónica sin secretos versionados, creación completa del esquema mediante migraciones y capacidad de revertir y reaplicar la cadena sin drift.

## Requirements

### Requirement: Configuración asincrónica sin credenciales versionadas

Alembic SHALL ejecutarse con motor asincrónico y SHALL obtener la URL de la misma configuración que la aplicación, armada con `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` y `POSTGRES_PORT` (driver `postgresql+asyncpg`), definidas en el entorno o en un `.env` local no versionado. `alembic.ini` NO SHALL contener usuario, clave ni URL de conexión. Si falta una variable obligatoria, la ejecución MUST fallar nombrándola, sin incluir valores.

#### Scenario: URL tomada del entorno

- **WHEN** se ejecuta `alembic upgrade head` con las variables `POSTGRES_*` definidas
- **THEN** Alembic se conecta con la URL `postgresql+asyncpg://…` armada a partir de ellas usando un motor asincrónico
- **AND** `alembic.ini` no contiene credenciales

#### Scenario: Falta DATABASE_URL

- **WHEN** se ejecuta Alembic con solo `DATABASE_URL` definida y sin las variables `POSTGRES_*`
- **THEN** `DATABASE_URL` se ignora y la ejecución falla con un error que nombra la variable `POSTGRES_*` que falta
- **AND** el mensaje no expone ningún valor de conexión

#### Scenario: Falta la contraseña de la base

- **WHEN** se ejecuta Alembic sin `POSTGRES_PASSWORD` en el entorno ni en `.env`
- **THEN** falla con un error que indica que falta `POSTGRES_PASSWORD`
- **AND** el mensaje no expone ningún valor de conexión

### Requirement: Esquema completo creado por migraciones

Una base vacía SHALL quedar con el esquema completo al ejecutar `alembic upgrade head`. El esquema MUST contener las 14 tablas: `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`, `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`, más el trigger de solo agregado. La cadena SHALL ser `0001 → 0002 → 0003 → 0004`, con 0001 y 0002 sin modificar. La aplicación y los tests NO SHALL usar `create_all`.

#### Scenario: Base vacía migrada

- **WHEN** se ejecuta `alembic upgrade head` contra una base PostgreSQL vacía
- **THEN** existen las 14 tablas del metadata con sus restricciones e índices y el trigger sobre `movimiento_stock`
- **AND** la revisión actual es `0004`

#### Scenario: Migraciones del TP intactas

- **WHEN** se comparan `0001` y `0002` con su versión anterior a este change
- **THEN** no tienen diferencias

#### Scenario: Sin creación automática de esquema

- **WHEN** se busca `create_all` en `app/`, `scripts/` y `test/`
- **THEN** no existe ninguna llamada que cree tablas fuera de Alembic

### Requirement: Migraciones reversibles y sin drift

La cadena de migraciones SHALL poder revertirse por completo y reaplicarse sin errores. El esquema migrado MUST coincidir con el metadata de los modelos, de modo que `alembic check` no detecte operaciones pendientes. El `downgrade` de 0004 SHALL quitar el trigger y su función, y el de 0003 SHALL restaurar el esquema de 0002, incluido el UNIQUE común del ISBN.

#### Scenario: Ciclo completo sobre base vacía

- **WHEN** se ejecuta `alembic upgrade head`, luego `alembic downgrade base` y otra vez `alembic upgrade head` sobre una base vacía
- **THEN** las tres operaciones terminan sin error
- **AND** tras `downgrade base` no queda ninguna tabla del dominio ni la función del trigger, y al final la cabeza es `0004`

#### Scenario: Ciclo downgrade y upgrade

- **WHEN** se ejecuta `alembic downgrade -1` y luego `alembic upgrade head` sobre una base migrada
- **THEN** ambas operaciones terminan sin error
- **AND** el esquema vuelve a la cabeza `0004`

#### Scenario: Revertir solo el trigger

- **WHEN** se ejecuta `alembic downgrade -1` desde `0004` y luego `alembic upgrade head`
- **THEN** en `0003` un `UPDATE` sobre `movimiento_stock` se acepta, y tras volver a `0004` se rechaza

#### Scenario: Sin drift entre modelos y migraciones

- **WHEN** se ejecuta `alembic check` contra una base migrada a `0004`
- **THEN** responde “No new upgrade operations detected”

### Requirement: Migraciones nuevas revisadas y documentadas
Cada migración nueva SHALL llevar en su encabezado un comentario que diga que se leyó antes de aplicarla y, si se corrigió lo generado, qué y por qué. La 0003 SHALL generarse con `--autogenerate`; la 0004 SHALL escribirse a mano y su comentario SHALL explicar que la comparación automática no ve funciones ni triggers.

#### Scenario: Encabezado de 0003
- **WHEN** se lee el archivo de la migración `0003`
- **THEN** su docstring indica que se generó con `--autogenerate`, que se revisó antes de aplicarla y qué se corrigió (o que no hizo falta)

#### Scenario: Encabezado de 0004
- **WHEN** se lee el archivo de la migración `0004`
- **THEN** su docstring indica que se escribió a mano, que se leyó antes de aplicarla y por qué no puede autogenerarse
