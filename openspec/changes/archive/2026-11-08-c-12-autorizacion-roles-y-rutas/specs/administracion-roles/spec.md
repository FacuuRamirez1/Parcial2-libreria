# Spec Delta

## Purpose

Define cómo el administrador consulta, asigna con vencimiento opcional y revoca los roles de un usuario, conservando siempre el historial y sin que el sistema pueda quedarse sin administradores.

## ADDED Requirements

### Requirement: Historial de roles de un usuario
`GET /usuarios/{id}/roles` SHALL devolver 200 con todas las asignaciones del usuario (vigentes, vencidas y revocadas), cada una con `id`, `rol`, `desde`, `vence_en`, `revocada_en`, `otorgada_por` y `vigente`, ordenadas por `desde`. Si el usuario no existe SHALL responder 404.

#### Scenario: Asignación revocada en el historial
- **WHEN** un administrador revoca `VENDEDOR` a un usuario y luego pide `GET /usuarios/{id}/roles`
- **THEN** la asignación aparece con `revocada_en` no nulo y `"vigente": false`

#### Scenario: Usuario inexistente
- **WHEN** un administrador pide `GET /usuarios/999999/roles`
- **THEN** la respuesta es 404 con un mensaje propio

### Requirement: Contrato de la asignación de rol
`POST /usuarios/{id}/roles` SHALL aceptar solo `rol` (`ADMIN`, `VENDEDOR` o `CLIENTE`) y `vence_en` opcional. Un `vence_en` sin zona horaria o que no esté en el futuro SHALL responder 422 (no 409), igual que un rol desconocido o un campo de más.

#### Scenario: Vencimiento sin zona horaria
- **WHEN** un administrador envía `{"rol": "VENDEDOR", "vence_en": "2030-01-01T10:00:00"}`
- **THEN** la respuesta es 422 y no se crea ninguna asignación

#### Scenario: Vencimiento en el pasado
- **WHEN** un administrador envía `{"rol": "VENDEDOR", "vence_en": "2020-01-01T10:00:00-03:00"}`
- **THEN** la respuesta es 422 y no se crea ninguna asignación

#### Scenario: Rol desconocido
- **WHEN** un administrador envía `{"rol": "GERENTE"}`
- **THEN** la respuesta es 422

### Requirement: Asignación de un rol nuevo
Una asignación válida SHALL crear una `asignacion_rol` abierta con el rol, el `vence_en` pedido (o nulo) y `otorgada_por` = administrador que la hace, y SHALL responder 201 con la asignación. Si el usuario no existe SHALL responder 404, detectado por la clave foránea y sin consultarlo antes.

#### Scenario: Asignación con vencimiento
- **WHEN** un administrador asigna `VENDEDOR` con `vence_en` dentro de un año, con zona, a un usuario que no lo tiene
- **THEN** la respuesta es 201 con `"vigente": true` y ese `vence_en`
- **AND** el usuario pasa a tener `VENDEDOR` entre sus roles vigentes

#### Scenario: Asignación a un usuario inexistente
- **WHEN** un administrador envía `POST /usuarios/999999/roles` con `{"rol": "VENDEDOR"}`
- **THEN** la respuesta es 404 con un mensaje propio y no queda ningún `evento_seguridad` nuevo

### Requirement: Rol vigente repetido rechazado
Asignar un rol que el usuario ya tiene vigente SHALL responder 409 con `{"detail": "El usuario ya tiene ese rol vigente"}` sin crear filas (RN-03). La unicidad de la asignación abierta SHALL seguir garantizada por el índice único parcial, que también responde 409 si dos asignaciones se cruzan.

#### Scenario: Asignar dos veces el mismo rol
- **WHEN** un administrador asigna `VENDEDOR` a `vendedor@example.com`, que ya lo tiene vigente
- **THEN** la respuesta es 409 con ese mensaje
- **AND** sigue habiendo una sola asignación abierta de `VENDEDOR` para ese usuario

### Requirement: Reasignación de un rol vencido
Asignar un rol cuya asignación abierta ya venció SHALL, en una sola transacción, cerrar esa fila (escribir su `revocada_en`) y abrir una nueva con los datos pedidos, y SHALL responder 201. La fila vencida NO SHALL borrarse.

#### Scenario: Rol vencido reasignado
- **WHEN** un usuario tiene una asignación abierta de `VENDEDOR` con `vence_en` en el pasado y un administrador le asigna `VENDEDOR` sin vencimiento
- **THEN** la respuesta es 201
- **AND** la fila anterior tiene `revocada_en` no nulo y existe una nueva abierta sin vencimiento

### Requirement: Revocación sin borrar la fila
`DELETE /usuarios/{id}/roles/{rol}` SHALL escribir `revocada_en` en la asignación abierta de ese rol y responder 200 con la asignación revocada; la fila NO SHALL borrarse. Si el usuario no existe o no tiene una asignación abierta de ese rol SHALL responder 404; un `{rol}` fuera de los tres roles SHALL responder 422.

#### Scenario: Revocación de un vendedor
- **WHEN** un administrador envía `DELETE /usuarios/{id del vendedor}/roles/VENDEDOR`
- **THEN** la respuesta es 200 con `revocada_en` no nulo
- **AND** la fila sigue en `asignacion_rol` (caso C-07 de la consigna)

#### Scenario: Revocar un rol que no tiene
- **WHEN** un administrador revoca `ADMIN` a un vendedor que nunca lo tuvo
- **THEN** la respuesta es 404

#### Scenario: Rol inválido en la ruta
- **WHEN** un administrador envía `DELETE /usuarios/1/roles/GERENTE`
- **THEN** la respuesta es 422

### Requirement: Autoprotección del administrador
Un administrador NO SHALL poder revocarse su propio rol `ADMIN`, y ninguna revocación SHALL dejar al sistema sin al menos un usuario activo con `ADMIN` vigente (RN-05); en ambos casos la respuesta SHALL ser 409 con un mensaje propio y nada SHALL cambiar.

#### Scenario: Administrador que se revoca su ADMIN
- **WHEN** `admin@example.com` envía `DELETE /usuarios/{su propio id}/roles/ADMIN`
- **THEN** la respuesta es 409 con `{"detail": "Un administrador no puede revocarse su propio rol ADMIN"}` (caso C-08 de la consigna)
- **AND** su asignación sigue abierta y no se agrega ningún `evento_seguridad`

#### Scenario: Último administrador vigente
- **WHEN** solo queda un usuario activo con `ADMIN` vigente y se intenta revocar ese `ADMIN`
- **THEN** la respuesta es 409 y el sistema conserva a su administrador

#### Scenario: Revocar a otro administrador
- **WHEN** `admin@example.com` revoca `ADMIN` a `admin2@example.com` y ambos lo tienen vigente
- **THEN** la respuesta es 200

#### Scenario: Revocarse un rol que no es ADMIN
- **WHEN** un administrador que además es VENDEDOR se revoca su propio `VENDEDOR`
- **THEN** la respuesta es 200
