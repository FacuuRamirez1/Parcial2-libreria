# cambio-password Specification

## Purpose

Define el cambio de contraseña del usuario autenticado: qué verifica, qué escribe de forma atómica junto con el historial de seguridad y por qué la sesión abierta sigue sirviendo.

## Requirements

### Requirement: Contrato del cambio de contraseña
`POST /auth/cambiar-password` SHALL exigir sesión (401 sin sesión válida) y aceptar solo `password_actual` (1 carácter como mínimo, 72 bytes como máximo) y `password_nueva` (8 caracteres como mínimo, 72 bytes como máximo); un campo adicional o faltante SHALL responder 422.

#### Scenario: Sin sesión
- **WHEN** se envía `POST /auth/cambiar-password` sin cookie
- **THEN** la respuesta es 401

#### Scenario: Nueva contraseña demasiado larga
- **WHEN** un usuario autenticado envía una `password_nueva` de 73 bytes
- **THEN** la respuesta es 422 y la contraseña no cambia

### Requirement: Contraseña actual verificada antes de cambiar
El sistema SHALL verificar `password_actual` contra el hash guardado del usuario y, si no coincide, SHALL responder 422 con `{"detail": "La contraseña actual no es correcta"}` sin modificar nada ni escribir eventos.

#### Scenario: Contraseña actual equivocada
- **WHEN** un usuario autenticado envía una `password_actual` incorrecta
- **THEN** la respuesta es 422 con ese mensaje
- **AND** su `password_hash` y su `debe_cambiar_password` no cambian y no se agrega ningún `evento_seguridad`

### Requirement: Cambio atómico con evento de seguridad
Un cambio válido SHALL, en una sola transacción, guardar el hash de la nueva contraseña, dejar `debe_cambiar_password = false` y agregar una fila en `evento_seguridad` con `actor` = correo del usuario y `accion = 'Cambio de contraseña'` (RN-16). La respuesta SHALL ser 200 con `{"mensaje": "Contraseña actualizada"}`.

#### Scenario: Cambio exitoso
- **WHEN** un usuario autenticado envía su contraseña actual correcta y una nueva válida
- **THEN** la respuesta es 200 con `{"mensaje": "Contraseña actualizada"}`
- **AND** la contraseña anterior ya no sirve para iniciar sesión y la nueva sí
- **AND** existe un `evento_seguridad` con su correo como `actor` y `accion = 'Cambio de contraseña'`

#### Scenario: Cambio que levanta la obligación
- **WHEN** un usuario con `debe_cambiar_password = true` cambia su contraseña
- **THEN** su `debe_cambiar_password` queda en `false`

#### Scenario: Falla al escribir el evento
- **WHEN** la actualización del usuario se hace pero la inserción del evento es rechazada por la base
- **THEN** el hash del usuario y `debe_cambiar_password` quedan como estaban

### Requirement: Sin token nuevo ni invalidación de sesiones
El cambio de contraseña NO SHALL emitir un token nuevo ni una cabecera `Set-Cookie`, y NO SHALL invalidar las sesiones abiertas: la misma cookie SHALL seguir sirviendo hasta que venza (DD-11).

#### Scenario: La misma cookie sigue sirviendo
- **WHEN** un usuario cambia su contraseña y luego envía `GET /auth/yo` con la misma cookie
- **THEN** la respuesta del cambio no trae `Set-Cookie`
- **AND** `GET /auth/yo` responde 200 con `"debe_cambiar_password": false`
