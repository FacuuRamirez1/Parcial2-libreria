# Spec Delta

## Purpose

Define cómo un administrador da de alta a un miembro del personal: con una contraseña provisoria que obliga a cambiarla, su rol y su línea en el historial de seguridad, todo de forma atómica.

## ADDED Requirements

### Requirement: Contrato del alta de personal
`POST /usuarios` SHALL aceptar solo `email` (hasta 254 caracteres, con formato de correo, guardado sin espacios y en minúsculas), `nombre` (1 a 120 caracteres), `password` (contraseña provisoria: al menos 8 caracteres y como máximo 72 bytes) y `rol` (`ADMIN` o `VENDEDOR`). Un campo adicional o faltante, o un rol fuera de esos dos, SHALL responder 422.

#### Scenario: Rol de cliente en el alta de personal
- **WHEN** un administrador envía `POST /usuarios` con `"rol": "CLIENTE"`
- **THEN** la respuesta es 422 y no se crea ninguna fila

#### Scenario: Campo de más
- **WHEN** un administrador envía `POST /usuarios` con un campo `"debe_cambiar_password": false`
- **THEN** la respuesta es 422

#### Scenario: Contraseña provisoria de 73 bytes
- **WHEN** un administrador envía `POST /usuarios` con una `password` de 73 bytes
- **THEN** la respuesta es 422 y el cuerpo no contiene la contraseña

### Requirement: Alta atómica con rol, cambio obligatorio y evento
Un alta válida SHALL crear en una sola transacción el `usuario` (activo, `debe_cambiar_password = true`, contraseña provisoria guardada con bcrypt), una `asignacion_rol` abierta con el rol pedido, sin vencimiento y con `otorgada_por` = administrador que la hace, y una fila en `evento_seguridad` con `actor` = correo del administrador (RN-16). O quedan las tres filas o ninguna.

#### Scenario: Alta de un vendedor
- **WHEN** un administrador envía `POST /usuarios` con `email`, `nombre`, `password` y `"rol": "VENDEDOR"`
- **THEN** la respuesta es 201 con `id`, `email`, `nombre`, `"debe_cambiar_password": true` y `"roles_vigentes": ["VENDEDOR"]`, sin `password_hash`
- **AND** existe un `evento_seguridad` cuyo `actor` es el correo del administrador y cuya `accion` nombra el alta, el correo nuevo y el rol

#### Scenario: El personal nuevo debe cambiar la contraseña
- **WHEN** el usuario recién dado de alta inicia sesión con la contraseña provisoria y envía `POST /ventas/`
- **THEN** el login responde 200 con `"debe_cambiar_password": true` y la venta responde 403

#### Scenario: Falla al escribir el evento
- **WHEN** el usuario y la asignación se insertan pero la inserción del evento es rechazada por la base
- **THEN** no queda ni el usuario ni la asignación

### Requirement: Correo repetido en el alta de personal
Un alta con un correo que ya tiene un usuario SHALL responder 409 con `{"detail": "El correo ya está registrado"}` sin consultar antes la existencia del correo: lo rechaza la restricción de unicidad de la base. No SHALL quedar ninguna fila nueva.

#### Scenario: Correo de un usuario existente
- **WHEN** un administrador envía `POST /usuarios` con `"email": "vendedor@example.com"`, que ya existe
- **THEN** la respuesta es 409 con ese mensaje, sin texto de la base
- **AND** no se agrega ninguna `asignacion_rol` ni ningún `evento_seguridad`

#### Scenario: Correo de un cliente sin usuario
- **WHEN** un administrador da de alta personal con el correo de un cliente del mostrador que no tiene usuario
- **THEN** la respuesta es 201 y la ficha del cliente no cambia (su `usuario_id` sigue nulo)

### Requirement: Contraseña provisoria fuera de la transacción
El hash de la contraseña provisoria SHALL calcularse fuera del bucle de eventos, bajo el limitador de concurrencia de bcrypt y sin una conexión de la base tomada mientras se calcula.

#### Scenario: Conexión libre durante bcrypt
- **WHEN** con el registro del pool activo un administrador envía `POST /usuarios`
- **THEN** la conexión de la petición se devuelve al pool antes de calcular el hash y se vuelve a tomar para las tres inserciones
