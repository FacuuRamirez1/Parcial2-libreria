# Spec Delta: data-model-conventions

## MODIFIED Requirements

### Requirement: Nombres de tablas y columnas de la consigna

El esquema SHALL contener las 9 tablas de la consigna `editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta` y `renglon_venta`, con los nombres de columna de la consigna. MAY contener además las tablas de infraestructura `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`. Se SHALL poder agregar columnas, pero nunca renombrar ni quitar las de la consigna.

#### Scenario: Inventario de tablas

- **WHEN** se cargan todos los modelos y se listan las tablas del metadata
- **THEN** el conjunto es exactamente {`editorial`, `genero`, `autor`, `libro`, `libro_autor`, `cliente`, `perfil_cliente`, `venta`, `renglon_venta`, `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`, `movimiento_stock`}

### Requirement: Modelos ubicados en su módulo funcional

Cada modelo de tabla, con sus columnas, restricciones y relaciones, SHALL definirse en el `models.py` de su módulo funcional. Ningún archivo fuera de `app/modules/<módulo>/models.py` SHALL definir tablas, columnas, restricciones ni relaciones.

#### Scenario: Ubicación de cada clase

- **WHEN** se carga el agregador de modelos y se consulta el módulo de origen de cada una de las 14 clases de tabla
- **THEN** cada clase proviene del `models.py` de su módulo: las 9 de la consigna de `editoriales`, `generos`, `autores`, `libros`, `clientes` o `ventas`, con `LibroAutor` y `MovimientoStock` en `libros`; y `Usuario`, `AsignacionRol`, `IntentoAcceso` y `EventoSeguridad` de `usuarios`

#### Scenario: Convención de nombres sin dominio

- **WHEN** se inspecciona el módulo que define la convención de nombres de restricciones e índices
- **THEN** sólo contiene la convención y su asignación al metadata, sin tablas, columnas, restricciones ni imports de módulos de dominio

### Requirement: Agregador único de modelos sin lógica de dominio

El sistema SHALL ofrecer un único punto de importación que reúne los 14 modelos de tabla desde sus módulos en el mismo metadata, de modo que las migraciones y el script de datos iniciales vean el esquema completo, y SHALL poder resolverse todas las relaciones sin errores tras esa importación. Ese punto SHALL limitarse a importar y reexportar las clases: NO SHALL definir tablas, columnas, restricciones, relaciones ni funciones.

#### Scenario: Importación del agregador

- **WHEN** se importa el agregador de modelos en un intérprete nuevo y se configuran los mappers
- **THEN** no se produce ningún error y el metadata contiene las 14 tablas

#### Scenario: Agregador sin definiciones

- **WHEN** se inspecciona el agregador de modelos
- **THEN** sólo contiene imports desde `app.modules.<módulo>.models` y la lista de nombres exportados
