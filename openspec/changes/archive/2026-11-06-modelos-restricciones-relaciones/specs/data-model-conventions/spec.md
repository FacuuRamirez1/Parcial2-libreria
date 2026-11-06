# Spec Delta

## Purpose

Fija las reglas transversales que cumplen todas las tablas del sistema: nombres exactos de la consigna, modelos ubicados en su módulo funcional, texto con largo máximo, nombres deterministas de restricciones e índices, índices en claves foráneas, un único agregador de modelos sin lógica de dominio, ausencia de carga perezosa, creación del esquema sólo mediante migraciones y restricciones nombradas que respaldan los casos de prueba de la consigna.

## ADDED Requirements

### Requirement: Nombres de tablas y columnas de la consigna
El esquema SHALL contener exactamente las tablas `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta` y `renglon_venta`, con los nombres de columna de la consigna. Se SHALL poder agregar columnas, pero nunca renombrar ni quitar las de la consigna.

#### Scenario: Inventario de tablas
- **WHEN** se cargan todos los modelos y se listan las tablas del metadata
- **THEN** el conjunto de nombres es exactamente {`editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`}

### Requirement: Modelos ubicados en su módulo funcional
Cada modelo de tabla, con sus columnas, restricciones y relaciones, SHALL definirse en el `models.py` de su módulo funcional (`editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`); `LibroAutor` SHALL vivir en `libros`, `PerfilCliente` en `clientes` y `RenglonVenta` en `ventas`. Ningún archivo fuera de `app/modules/<módulo>/models.py` SHALL definir tablas, columnas, restricciones ni relaciones.

#### Scenario: Ubicación de cada clase
- **WHEN** se carga el agregador de modelos y se consulta el módulo de origen de cada una de las 9 clases de tabla
- **THEN** cada clase proviene de `app.modules.<módulo>.models` según la tabla de módulos, y ninguna de otro módulo

#### Scenario: Convención de nombres sin dominio
- **WHEN** se inspecciona el módulo que define la convención de nombres de restricciones e índices
- **THEN** sólo contiene la convención y su asignación al metadata, sin tablas, columnas, restricciones ni imports de módulos de dominio

### Requirement: Texto siempre con largo máximo
Toda columna de texto SHALL tener un largo máximo físico en la base (`VARCHAR(n)`); ninguna columna de texto SHALL quedar sin largo. La validación de largo y formato en los contratos de entrada es una capa adicional y no reemplaza este límite.

#### Scenario: Ningún texto sin largo
- **WHEN** se inspeccionan los tipos de todas las columnas de texto del metadata
- **THEN** todas son `VARCHAR(n)` y ninguna es `VARCHAR` sin largo ni `TEXT`

#### Scenario: Largos de cada columna de texto
- **WHEN** se compila el DDL de las 9 tablas para PostgreSQL
- **THEN** los largos son `editorial.nombre` 120, `editorial.pais` 60, `genero.nombre` 60, `autor.nombre` 120, `autor.nacionalidad` 60, `libro.isbn` 17, `libro.titulo` 255, `libro_autor.rol` 20, `cliente.nombre` 120, `cliente.email` 254, `perfil_cliente.telefono` 30 y `perfil_cliente.direccion` 255

#### Scenario: Texto que excede el largo
- **WHEN** se intenta guardar directamente en la base un valor más largo que el `n` de su columna
- **THEN** la base rechaza la escritura

### Requirement: Dinero siempre en decimal exacto
Toda columna que representa dinero SHALL ser `NUMERIC` con precisión y escala fijas y SHALL manejarse en Python como `Decimal`; ninguna columna de dinero SHALL ser de coma flotante.

#### Scenario: Ninguna columna flotante
- **WHEN** se inspeccionan los tipos de todas las columnas del metadata
- **THEN** ninguna es `FLOAT`, `REAL` ni `DOUBLE PRECISION`

### Requirement: Nombres deterministas de restricciones e índices
Toda clave primaria, clave foránea, restricción UNIQUE, restricción CHECK e índice SHALL tener un nombre explícito y predecible derivado de la tabla y la columna, sin depender de los nombres que asigne PostgreSQL, para que las migraciones puedan crearlos y borrarlos por nombre.

#### Scenario: Nombre de un CHECK
- **WHEN** se compila el DDL de `libro` para PostgreSQL
- **THEN** la restricción de precio positivo aparece con un nombre que comienza con `ck_libro_`

#### Scenario: Nombre de una clave foránea
- **WHEN** se compila el DDL de `libro` para PostgreSQL
- **THEN** la FK de `genero_id` aparece con el nombre `fk_libro_genero_id_genero`

### Requirement: Índice en cada clave foránea
Cada columna que es clave foránea SHALL estar cubierta por un índice, ya sea propio, por ser primera columna de la clave primaria o por una restricción UNIQUE. En particular SHALL existir índices propios en `libro.editorial_id`, `libro.genero_id`, `libro_autor.autor_id`, `venta.cliente_id`, `renglon_venta.venta_id` y `renglon_venta.libro_id`.

#### Scenario: Índices de libro
- **WHEN** se listan los índices de la tabla `libro`
- **THEN** hay uno sobre `editorial_id` y otro sobre `genero_id`

#### Scenario: FK cubierta por otra restricción
- **WHEN** se inspeccionan `libro_autor.libro_id` y `perfil_cliente.cliente_id`
- **THEN** la primera está cubierta por la clave primaria compuesta y la segunda por su restricción UNIQUE, sin índice duplicado

### Requirement: Agregador único de modelos sin lógica de dominio
El sistema SHALL ofrecer un único punto de importación que reúne los 9 modelos de tabla desde sus módulos en el mismo metadata, de modo que las migraciones y el script de datos iniciales vean el esquema completo, y SHALL poder resolverse todas las relaciones sin errores tras esa importación. Ese punto SHALL limitarse a importar y reexportar las clases: NO SHALL definir tablas, columnas, restricciones, relaciones ni funciones.

#### Scenario: Importación del agregador
- **WHEN** se importa el agregador de modelos en un intérprete nuevo y se configuran los mappers
- **THEN** no se produce ningún error y el metadata contiene las 9 tablas

#### Scenario: Agregador sin definiciones
- **WHEN** se inspecciona el agregador de modelos
- **THEN** sólo contiene imports desde `app.modules.<módulo>.models` y la lista de nombres exportados

### Requirement: Sin carga perezosa de relaciones
Ninguna relación SHALL cargarse en forma perezosa. Acceder a una relación que no fue precargada en la consulta SHALL fallar de inmediato con un error, en lugar de emitir SQL oculto (NF-04). La precarga explícita en la consulta SHALL seguir funcionando.

#### Scenario: Acceso a una relación no precargada
- **WHEN** se lee un libro sin precargar su editorial y se accede a `editorial`
- **THEN** se produce un error inmediato y no se emite ninguna sentencia SQL

#### Scenario: Relación precargada
- **WHEN** se lee un libro precargando su editorial en la misma consulta
- **THEN** el acceso a la editorial funciona sin sentencias adicionales

### Requirement: Esquema creado sólo por migraciones
El código de la aplicación NO SHALL crear tablas por su cuenta (ni al importar los modelos ni al arrancar, ni en bases de prueba o descartables); importar los modelos NO SHALL abrir conexiones a la base.

#### Scenario: Importar modelos sin base
- **WHEN** se importan todos los modelos con PostgreSQL apagado y sin `DATABASE_URL`
- **THEN** la importación termina sin error y no se intenta ninguna conexión

#### Scenario: Sin creación automática de tablas
- **WHEN** se busca en el código de la aplicación una creación de esquema fuera de las migraciones
- **THEN** no existe ninguna llamada de ese tipo

### Requirement: Restricciones que respaldan los casos de prueba de la consigna
Cada caso de prueba de la consigna (C-02 a C-05) que depende de una garantía de la base SHALL estar respaldado por una restricción con nombre determinista. Su aceptación SHALL demostrarse con peticiones `.http` de `test/` contra PostgreSQL 16 con el esquema creado por las migraciones, con la respuesta esperada en un comentario.

#### Scenario: Traspaso de la aceptación
- **WHEN** se revisan los archivos que crea este change
- **THEN** no incluyen ningún `.http`; los escenarios HTTP los escriben y ejecutan C-04 y C-05 (C-06 para el detalle sin N+1) y la verificación del DDL real y de los CHECK/largos la hace C-03

#### Scenario: Restricciones presentes para los casos de prueba
- **WHEN** se compila el DDL de todas las tablas para PostgreSQL
- **THEN** existen `uq_cliente_email` y `uq_libro_isbn` (caso C-02), `uq_perfil_cliente_cliente_id` (C-03), `fk_libro_editorial_id_editorial` y `fk_libro_autor_autor_id_autor` (C-04), y `fk_venta_cliente_id_cliente` y `fk_renglon_venta_libro_id_libro` (C-05)

#### Scenario: Email repetido demostrado por HTTP
- **WHEN** (escenario a ejecutar en C-04) con el esquema creado por las migraciones y los datos iniciales cargados, el archivo `.http` envía un alta de cliente con un email ya registrado
- **THEN** la respuesta es 409 con un mensaje propio, sin texto interno de la base

#### Scenario: Editorial inexistente demostrada por HTTP
- **WHEN** (escenario a ejecutar en C-05) con el esquema creado por las migraciones, el archivo `.http` envía un alta de libro con un `editorial_id` inexistente
- **THEN** la respuesta es 409 con un mensaje propio, porque la base rechazó la clave foránea

