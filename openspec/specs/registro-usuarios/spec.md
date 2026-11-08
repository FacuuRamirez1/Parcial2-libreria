# registro-usuarios Specification

## Purpose

Define el auto-registro de un cliente en la web: qué datos acepta, qué filas crea de forma atómica, cómo se protege la unicidad del correo y qué devuelve.

## Requirements

### Requirement: Contrato de entrada del registro
`POST /auth/registro` SHALL aceptar solo `email` (hasta 254 caracteres, con formato de correo), `nombre` (1 a 120 caracteres) y `password` (al menos 8 caracteres y como máximo 72 bytes). Cualquier campo adicional, como `rol` o `activo`, SHALL rechazarse con 422. El correo SHALL guardarse sin espacios alrededor y en minúsculas.

#### Scenario: Intento de registrarse con un rol
- **WHEN** se envía `POST /auth/registro` con `email`, `nombre`, `password` y `"rol": "ADMIN"`
- **THEN** la respuesta es 422 y no se crea ninguna fila

#### Scenario: Correo sin formato válido
- **WHEN** se envía `POST /auth/registro` con `"email": "no-es-un-correo"`
- **THEN** la respuesta es 422

#### Scenario: Contraseña demasiado corta
- **WHEN** se envía `POST /auth/registro` con una contraseña de 7 caracteres
- **THEN** la respuesta es 422

#### Scenario: Correo normalizado
- **WHEN** se registra `"email": "  Lucas@Example.COM "`
- **THEN** el usuario y la ficha de cliente quedan con `lucas@example.com`

### Requirement: Registro atómico de usuario, rol CLIENTE y ficha de cliente
Un registro válido SHALL crear en una sola transacción el `usuario` (activo, sin cambio de contraseña pendiente), una `asignacion_rol` abierta con rol `CLIENTE` y sin vencimiento, y un `cliente` con el mismo correo y nombre cuyo `usuario_id` apunta al usuario nuevo (RN-02). O quedan las tres filas o ninguna.

#### Scenario: Registro exitoso
- **WHEN** se envía `POST /auth/registro` con `{"email": "lucas@example.com", "nombre": "Lucas Gómez", "password": "clave-segura-1"}`
- **THEN** la respuesta es 201
- **AND** existen un `usuario` con ese correo, una `asignacion_rol` `CLIENTE` con `revocada_en` y `vence_en` nulos y un `cliente` con ese correo cuyo `usuario_id` es el id del usuario

#### Scenario: Falla al crear la ficha de cliente
- **WHEN** el usuario y el rol se insertan pero la inserción del `cliente` es rechazada por la base
- **THEN** no queda en la base ni el usuario ni la asignación de rol

### Requirement: Correo repetido rechazado sin apropiarse de fichas existentes
Si el correo ya pertenece a un usuario o a un cliente, el registro SHALL responder 409 con un mensaje propio que no contenga texto de la base, SHALL no dejar ninguna fila nueva y NO SHALL vincular ni modificar la ficha de cliente existente. La unicidad SHALL garantizarla la base, sin consulta previa del correo.

#### Scenario: Correo de un usuario existente
- **WHEN** se registra dos veces `lucas@example.com`
- **THEN** la segunda respuesta es 409 con `{"detail": "El correo ya está registrado"}`
- **AND** sigue habiendo un solo usuario, una sola asignación y un solo cliente con ese correo

#### Scenario: Correo de un cliente cargado en el mostrador
- **WHEN** existe un `cliente` con `email = 'tomas@example.com'` y `usuario_id` nulo, y se envía `POST /auth/registro` con ese correo
- **THEN** la respuesta es 409 con `{"detail": "El correo ya está registrado"}`
- **AND** no se crea ningún usuario ni asignación, y ese cliente conserva `usuario_id` nulo

### Requirement: Respuesta del registro sin sesión ni datos sensibles
El registro exitoso SHALL responder 201 con `id`, `email`, `nombre` y `cliente_id`, NO SHALL incluir `password_hash` ni la contraseña y NO SHALL iniciar sesión: la respuesta no lleva `Set-Cookie` (SU-10).

#### Scenario: Cuerpo y cabeceras del 201
- **WHEN** un registro responde 201
- **THEN** el cuerpo tiene exactamente `id`, `email`, `nombre` y `cliente_id`
- **AND** la respuesta no trae la cabecera `Set-Cookie`
