# Spec Delta

## Purpose

Define el esquema de acceso del Parcial: usuarios, asignaciones de rol con vigencia, intentos de acceso y el historial de seguridad, con las restricciones que la base garantiza por sí misma, sin incluir lógica de autenticación ni de autorización.

## ADDED Requirements

### Requirement: Tabla usuario con correo único y sin rol
El esquema SHALL incluir la tabla `usuario` con `id`, `email`, `nombre`, `password_hash`, `activo` y `debe_cambiar_password`, todas obligatorias. `email` SHALL ser único (RN-01). La tabla NO SHALL tener una columna `rol`: los roles viven en `asignacion_rol`.

#### Scenario: Correo de usuario repetido
- **WHEN** se intenta guardar un segundo usuario con un `email` ya registrado
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Columnas de usuario
- **WHEN** se inspecciona el DDL de `usuario` en PostgreSQL
- **THEN** existen exactamente `id`, `email`, `nombre`, `password_hash`, `activo` y `debe_cambiar_password`, y no existe ninguna columna `rol`

#### Scenario: Valores iniciales de las banderas
- **WHEN** se guarda un usuario sin indicar `activo` ni `debe_cambiar_password`
- **THEN** queda con `activo = true` y `debe_cambiar_password = false`

### Requirement: Tabla asignacion_rol con rol válido
El esquema SHALL incluir la tabla `asignacion_rol` con `id`, `usuario_id` (FK a `usuario`, obligatoria), `rol`, `desde`, `vence_en` (nulo), `revocada_en` (nulo) y `otorgada_por` (FK a `usuario`, nula). `rol` SHALL estar restringido por CHECK a `ADMIN`, `VENDEDOR` o `CLIENTE`. Las tres fechas SHALL ser `timestamptz`.

#### Scenario: Rol fuera del dominio
- **WHEN** se intenta guardar una asignación con `rol = 'SUPERVISOR'`
- **THEN** la base rechaza la escritura por violación del CHECK

#### Scenario: Asignación para un usuario inexistente
- **WHEN** se intenta guardar una asignación con un `usuario_id` que no existe
- **THEN** la base rechaza la escritura por violación de la clave foránea

#### Scenario: Fechas con zona horaria
- **WHEN** se inspecciona el DDL de `asignacion_rol`
- **THEN** `desde`, `vence_en` y `revocada_en` son `timestamp with time zone`, y `vence_en`, `revocada_en` y `otorgada_por` admiten nulo

### Requirement: Una sola asignación abierta por usuario y rol
La base SHALL garantizar, con un índice único parcial sobre `(usuario_id, rol)` limitado a las filas con `revocada_en IS NULL`, que un usuario tenga a lo sumo una asignación abierta por rol (RN-03). Las asignaciones revocadas NO SHALL contar para esa unicidad.

#### Scenario: Segunda asignación abierta del mismo rol
- **WHEN** un usuario ya tiene una asignación `VENDEDOR` con `revocada_en` nulo y se guarda otra `VENDEDOR` abierta para él
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Reasignación tras revocar
- **WHEN** la asignación `VENDEDOR` de un usuario tiene `revocada_en` con fecha y se guarda una nueva `VENDEDOR` abierta para él
- **THEN** la base acepta la escritura y conserva ambas filas

#### Scenario: Roles distintos abiertos a la vez
- **WHEN** un usuario tiene una asignación `ADMIN` abierta y se guarda una `VENDEDOR` abierta para él
- **THEN** la base acepta la escritura

### Requirement: Tabla intento_acceso sin relaciones
El esquema SHALL incluir la tabla `intento_acceso` con `id`, `cuando` (`timestamptz`), `email`, `ip` y `exito`, sin claves foráneas ni restricciones adicionales, y con un índice compuesto `(email, ip, cuando)` que sirva al conteo de intentos recientes.

#### Scenario: Intento con un correo que no es de ningún usuario
- **WHEN** se guarda un intento con un `email` que no existe en `usuario`
- **THEN** la base acepta la escritura

#### Scenario: Índice del conteo de intentos
- **WHEN** se listan los índices de `intento_acceso`
- **THEN** existe uno sobre las columnas `email`, `ip` y `cuando`, en ese orden

### Requirement: Tabla evento_seguridad con actor de texto
El esquema SHALL incluir la tabla `evento_seguridad` con `id`, `cuando` (`timestamptz`), `actor` y `accion`, sin claves foráneas ni restricciones adicionales. `actor` SHALL ser texto, de modo que admita un valor que no es un usuario, como `SISTEMA`.

#### Scenario: Evento del sistema
- **WHEN** se guarda un evento con `actor = 'SISTEMA'` y `accion = 'Carga de los datos iniciales'`
- **THEN** la base acepta la escritura

### Requirement: Navegación de acceso en ambos extremos
Desde un usuario SHALL navegarse a sus asignaciones de rol, a las asignaciones que otorgó, a su ficha de cliente (un objeto o ninguno) y a sus movimientos de stock; desde una asignación, a su usuario y a quien la otorgó. Toda navegación SHALL requerir precarga explícita.

#### Scenario: Asignaciones precargadas
- **WHEN** se lee un usuario precargando sus asignaciones
- **THEN** se obtiene la colección de sus asignaciones y cada una da acceso al mismo usuario

#### Scenario: Asignaciones sin precarga
- **WHEN** se lee un usuario sin precargar sus asignaciones y se accede a ellas
- **THEN** se produce un error inmediato y no se emite SQL

### Requirement: Texto de las tablas de acceso con largo máximo
Las columnas de texto de las tablas de acceso SHALL tener largo máximo: `usuario.email` e `intento_acceso.email` 254, `usuario.nombre` 120, `usuario.password_hash` 255, `asignacion_rol.rol` 20, `intento_acceso.ip` 45, `evento_seguridad.actor` 254 y `evento_seguridad.accion` 255.

#### Scenario: Correo más largo que la columna
- **WHEN** se intenta guardar directamente en la base un usuario con un `email` de 255 caracteres
- **THEN** la base rechaza la escritura por exceder el largo de la columna
