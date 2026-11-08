# customer-data Specification

## Purpose

Define el esquema de clientes y de su perfil opcional, garantizando en la base la unicidad y el largo máximo del email, el largo de los demás textos y que cada cliente tenga como máximo un perfil.

## Requirements

### Requirement: Tabla cliente con email único
El esquema SHALL incluir la tabla `cliente` con las columnas `id` (clave primaria entera generada por la base), `nombre` (`VARCHAR(120)`) y `email` (`VARCHAR(254)`), ambas obligatorias. El `email` SHALL ser único (RN-02).

#### Scenario: Email repetido
- **WHEN** se intenta guardar un segundo cliente con un `email` ya registrado
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Tipo de las columnas de cliente
- **WHEN** se inspecciona el DDL de `cliente` para PostgreSQL
- **THEN** `nombre` es `VARCHAR(120) NOT NULL` y `email` es `VARCHAR(254) NOT NULL`

#### Scenario: Email más largo que la columna
- **WHEN** se intenta guardar directamente en la base un cliente con un `email` de 255 caracteres
- **THEN** la base rechaza la escritura por exceder el largo de la columna

### Requirement: Tabla perfil_cliente
El esquema SHALL incluir la tabla `perfil_cliente` con las columnas `id` (clave primaria entera generada por la base), `cliente_id` (obligatoria, FK a `cliente.id`), `telefono` (`VARCHAR(30)` obligatorio) y `direccion` (`VARCHAR(255)` obligatorio).

#### Scenario: Perfil de un cliente inexistente
- **WHEN** se intenta guardar un perfil con un `cliente_id` que no corresponde a ningún cliente
- **THEN** la base rechaza la escritura por violación de clave foránea

### Requirement: Como máximo un perfil por cliente
`perfil_cliente.cliente_id` SHALL ser único, de modo que la base garantice la relación uno a uno (RN-09). Un cliente SHALL poder existir sin perfil (SU-05).

#### Scenario: Segundo perfil para el mismo cliente
- **WHEN** se intenta guardar un segundo perfil con el mismo `cliente_id`
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Cliente sin perfil
- **WHEN** se guarda un cliente y no se le crea perfil
- **THEN** la base acepta el cliente y no exige ninguna fila en `perfil_cliente`

### Requirement: Navegación cliente–perfil como objeto único
Desde un cliente SHALL navegarse a su perfil como un único objeto (o ninguno), nunca como una lista; desde un perfil SHALL navegarse a su cliente. Desde un cliente SHALL navegarse también a la colección de sus ventas.

#### Scenario: Perfil precargado
- **WHEN** se lee un cliente con su perfil precargado
- **THEN** el perfil se obtiene como un objeto con `telefono` y `direccion`, no como una colección

#### Scenario: Cliente sin perfil precargado
- **WHEN** se lee un cliente sin perfil con la relación precargada
- **THEN** el perfil del cliente es nulo
