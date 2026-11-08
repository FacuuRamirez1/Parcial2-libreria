# Spec Delta

## ADDED Requirements

### Requirement: Acceso web opcional del cliente
La tabla `cliente` SHALL tener la columna `usuario_id`, FK a `usuario`, nula y UNIQUE: un cliente puede tener o no acceso por la web, y un usuario está ligado a lo sumo a un cliente. `email` SHALL seguir siendo UNIQUE. La FK SHALL quedar cubierta por la restricción UNIQUE, sin índice duplicado.

#### Scenario: Cliente sin usuario
- **WHEN** se guarda un cliente sin indicar `usuario_id`
- **THEN** la base acepta la escritura y `usuario_id` queda nulo

#### Scenario: Varios clientes sin usuario
- **WHEN** existen dos clientes con `usuario_id` nulo
- **THEN** la unicidad no los rechaza

#### Scenario: Dos clientes con el mismo usuario
- **WHEN** se intenta ligar un segundo cliente a un `usuario_id` que ya tiene otro cliente
- **THEN** la base rechaza la escritura por violación de unicidad

#### Scenario: Usuario inexistente
- **WHEN** se intenta guardar un cliente con un `usuario_id` que no existe
- **THEN** la base rechaza la escritura por violación de la clave foránea

#### Scenario: Clientes existentes al migrar
- **WHEN** se aplica la migración sobre una base con clientes cargados
- **THEN** todos quedan con `usuario_id` nulo y conservan sus demás datos

### Requirement: Navegación cliente–usuario como objeto único
Desde un cliente SHALL navegarse a su usuario como un único objeto (o ninguno), nunca como una lista; desde un usuario SHALL navegarse a su cliente del mismo modo. La navegación SHALL requerir precarga explícita.

#### Scenario: Usuario precargado
- **WHEN** se lee un cliente con usuario precargando la relación
- **THEN** el usuario se obtiene como un objeto, no como una colección

#### Scenario: Cliente sin acceso web
- **WHEN** se lee un cliente sin usuario precargando la relación
- **THEN** el usuario del cliente es nulo
