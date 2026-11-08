# Spec Delta

## Purpose

Define el alta del perfil único de un cliente existente, con un contrato de entrada acotado y respuestas explícitas para cliente inexistente (409) y perfil duplicado (409).

## ADDED Requirements

### Requirement: Alta del perfil de un cliente
`POST /clientes/{id}/perfil` SHALL crear el perfil del cliente indicado en la ruta y responder 201 con `id`, `telefono`, `direccion` y `cliente_id`. El cuerpo SHALL contener `telefono` y `direccion` y SHALL rechazar campos desconocidos con 422 (`extra="forbid"`). Si el cuerpo incluye `cliente_id`, SHALL coincidir con el `id` de la ruta; en caso contrario la API SHALL responder 422.

#### Scenario: Alta correcta
- **WHEN** se envía `POST /clientes/1/perfil` con `telefono` y `direccion` válidos
- **THEN** la API responde 201 con el perfil creado y `cliente_id = 1`

#### Scenario: Cliente de la ruta distinto del cuerpo
- **WHEN** se envía `POST /clientes/1/perfil` con `cliente_id = 2` en el cuerpo
- **THEN** la API responde 422 y no crea el perfil

#### Scenario: Campo desconocido en el cuerpo
- **WHEN** se envía `POST /clientes/1/perfil` con un campo no previsto en el contrato
- **THEN** la API responde 422 y no crea el perfil

### Requirement: Perfil único por cliente
Un cliente SHALL tener como máximo un perfil (RN-09). La unicidad SHALL garantizarla la base y el segundo alta SHALL responder 409 con un mensaje propio, sin consultar antes si el cliente ya tiene perfil y sin devolver el nombre de la restricción ni texto del driver.

#### Scenario: Segundo perfil para el mismo cliente
- **WHEN** se envía `POST /clientes/{id}/perfil` para un cliente que ya tiene perfil
- **THEN** la API responde 409 con un mensaje propio y el perfil original permanece sin cambios

### Requirement: Cliente inexistente en el alta de perfil
Si el cliente indicado en la ruta no existe, la API SHALL responder 409 con un mensaje propio, distinto del mensaje de perfil duplicado, por consistencia con el resto de las altas con clave foránea. La aplicación NO SHALL consultar previamente la existencia del cliente ni SHALL devolver texto interno de la base.

#### Scenario: Perfil de un cliente inexistente
- **WHEN** se envía `POST /clientes/999999/perfil` con un cuerpo válido
- **THEN** la API responde 409 con un mensaje propio que indica que el cliente no existe, sin texto interno de la base, y no queda ningún perfil persistido

### Requirement: Validación de los datos del perfil
`telefono` SHALL respetar el largo máximo de la columna (`VARCHAR(30)`) y `direccion` el de la suya (`VARCHAR(255)`). Un valor que exceda el largo SHALL responder 422 con un mensaje propio.

#### Scenario: Teléfono demasiado largo
- **WHEN** se envía `POST /clientes/{id}/perfil` con un `telefono` de 31 caracteres
- **THEN** la API responde 422 y no crea el perfil
