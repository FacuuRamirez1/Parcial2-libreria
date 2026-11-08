# Spec Delta

## MODIFIED Requirements

### Requirement: Índice en cada clave foránea
Cada columna que es clave foránea SHALL estar cubierta por un índice, ya sea propio, por ser primera columna de la clave primaria o por una restricción UNIQUE. En particular SHALL existir índices propios en `libro.editorial_id`, `libro.genero_id`, `libro_autor.autor_id`, `venta.cliente_id`, `renglon_venta.venta_id`, `renglon_venta.libro_id`, `asignacion_rol.usuario_id`, `asignacion_rol.otorgada_por`, `movimiento_stock.libro_id`, `movimiento_stock.venta_id` y `movimiento_stock.usuario_id`.

#### Scenario: Índices de libro
- **WHEN** se listan los índices de la tabla `libro`
- **THEN** hay uno sobre `editorial_id` y otro sobre `genero_id`

#### Scenario: Índices de las FK nuevas
- **WHEN** se listan los índices de `asignacion_rol` y `movimiento_stock`
- **THEN** hay índices propios sobre `asignacion_rol.usuario_id`, `asignacion_rol.otorgada_por`, `movimiento_stock.libro_id`, `movimiento_stock.venta_id` y `movimiento_stock.usuario_id`

#### Scenario: FK cubierta por otra restricción
- **WHEN** se inspeccionan `libro_autor.libro_id`, `perfil_cliente.cliente_id` y `cliente.usuario_id`
- **THEN** la primera está cubierta por la clave primaria compuesta y las otras dos por su restricción UNIQUE, sin índice duplicado

### Requirement: Restricciones que respaldan los casos de prueba de la consigna
Cada caso de prueba de la consigna (C-02 a C-05) que depende de una garantía de la base SHALL estar respaldado por una restricción o índice con nombre determinista. Su aceptación SHALL demostrarse con peticiones `.http` de `test/` contra PostgreSQL 16 con el esquema creado por las migraciones, con la respuesta esperada en un comentario.

#### Scenario: Traspaso de la aceptación
- **WHEN** se revisan los archivos que crea este change
- **THEN** no incluyen ningún `.http`; los escenarios HTTP los escriben y ejecutan C-04 y C-05 (C-06 para el detalle sin N+1) y la verificación del DDL real y de los CHECK/largos la hace C-03

#### Scenario: Restricciones presentes para los casos de prueba
- **WHEN** se compila el DDL de todas las tablas para PostgreSQL
- **THEN** existen `uq_cliente_email` y el índice único parcial `ix_libro_isbn_vigente` (caso C-02), `uq_perfil_cliente_cliente_id` (C-03), `fk_libro_editorial_id_editorial` y `fk_libro_autor_autor_id_autor` (C-04), y `fk_venta_cliente_id_cliente` y `fk_renglon_venta_libro_id_libro` (C-05)

#### Scenario: Email repetido demostrado por HTTP
- **WHEN** (escenario a ejecutar en C-04) con el esquema creado por las migraciones y los datos iniciales cargados, el archivo `.http` envía un alta de cliente con un email ya registrado
- **THEN** la respuesta es 409 con un mensaje propio, sin texto interno de la base

#### Scenario: Editorial inexistente demostrada por HTTP
- **WHEN** (escenario a ejecutar en C-05) con el esquema creado por las migraciones, el archivo `.http` envía un alta de libro con un `editorial_id` inexistente
- **THEN** la respuesta es 409 con un mensaje propio, porque la base rechazó la clave foránea

## ADDED Requirements

### Requirement: Fechas nuevas con zona horaria
Toda columna de fecha agregada por el Parcial (`libro.borrado_en`, `asignacion_rol.desde`, `asignacion_rol.vence_en`, `asignacion_rol.revocada_en`, `intento_acceso.cuando`, `evento_seguridad.cuando` y `movimiento_stock.cuando`) SHALL ser `timestamp with time zone`.

#### Scenario: Inventario de fechas nuevas
- **WHEN** se consultan en `information_schema.columns` los tipos de esas siete columnas
- **THEN** todas son `timestamp with time zone`

### Requirement: Índices únicos parciales con nombre explícito
Los dos índices únicos parciales del esquema SHALL tener nombre explícito y estable: `ix_libro_isbn_vigente` sobre `libro(isbn)` con `borrado_en IS NULL`, y `ix_asignacion_rol_abierta` sobre `asignacion_rol(usuario_id, rol)` con `revocada_en IS NULL`, para que las migraciones puedan crearlos y borrarlos por nombre.

#### Scenario: Definición de los índices parciales
- **WHEN** se consulta `pg_indexes` para `libro` y `asignacion_rol`
- **THEN** `ix_libro_isbn_vigente` es `UNIQUE` sobre `isbn` con `WHERE (borrado_en IS NULL)` y `ix_asignacion_rol_abierta` es `UNIQUE` sobre `(usuario_id, rol)` con `WHERE (revocada_en IS NULL)`
