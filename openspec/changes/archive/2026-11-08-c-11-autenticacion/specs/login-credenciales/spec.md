# Spec Delta

## Purpose

Define cómo `POST /auth/login` verifica correo y contraseña sin revelar si una cuenta existe, en qué orden decide y qué devuelve cuando la sesión se inicia.

## ADDED Requirements

### Requirement: Contrato de entrada del login
`POST /auth/login` SHALL aceptar solo `email` (hasta 254 caracteres) y `password` (1 carácter como mínimo y 72 bytes como máximo); un campo adicional o faltante SHALL responder 422. El correo SHALL compararse sin espacios alrededor y en minúsculas.

#### Scenario: Campo extra en el login
- **WHEN** se envía `POST /auth/login` con `email`, `password` y `"recordar": true`
- **THEN** la respuesta es 422

#### Scenario: Correo con mayúsculas
- **WHEN** existe el usuario `lucas@example.com` y se envía el login con `"email": "LUCAS@example.com"` y su contraseña correcta
- **THEN** la sesión se inicia (200)

### Requirement: Orden de decisión del login
El login SHALL decidir en este orden: primero el límite de intentos (ver `limite-intentos-login`), que si se superó responde 429 sin calcular ningún hash; después la verificación de la contraseña; y solo si es correcta, la emisión de la sesión.

#### Scenario: Límite superado con contraseña correcta
- **WHEN** el correo y la IP ya superaron el límite y se envía la contraseña correcta
- **THEN** la respuesta es 429 y no se emite cookie

### Requirement: Respuesta indistinguible exista o no el correo
Con un correo inexistente, con una contraseña incorrecta o con un usuario inactivo, el login SHALL responder 401 con el mismo cuerpo `{"detail": "Correo o contraseña incorrectos"}`. Si el correo no existe, la contraseña SHALL verificarse igual contra un hash ficticio calculado al arrancar, de modo que el tiempo de respuesta sea parecido al de un correo existente (RN-08).

#### Scenario: Contraseña incorrecta de un correo existente
- **WHEN** se envía el login de `lucas@example.com` con una contraseña equivocada
- **THEN** la respuesta es 401 con `{"detail": "Correo o contraseña incorrectos"}` y sin `Set-Cookie`

#### Scenario: Correo inexistente
- **WHEN** se envía el login de `nadie@example.com`
- **THEN** la respuesta es 401 con exactamente el mismo cuerpo que el caso anterior
- **AND** su tiempo de respuesta es del mismo orden que el del caso anterior (los dos incluyen una verificación bcrypt), y no de pocos milisegundos

#### Scenario: Usuario inactivo con contraseña correcta
- **WHEN** un usuario con `activo = false` envía su contraseña correcta
- **THEN** la respuesta es 401 con el mismo cuerpo y sin `Set-Cookie`

### Requirement: Respuesta del login exitoso sin token en el cuerpo
Un login correcto SHALL responder 200 con el cuerpo `{"mensaje": "Sesión iniciada", "debe_cambiar_password": <bool del usuario>, "expira_en_segundos": <duración del token>}` y la cookie de sesión en `Set-Cookie` (ver `sesion-cookie`). El cuerpo NO SHALL contener el token ni ningún otro dato del usuario.

#### Scenario: Login correcto con la configuración por defecto
- **WHEN** `lucas@example.com` inicia sesión con su contraseña y `ACCESS_TOKEN_MINUTES=30`
- **THEN** la respuesta es 200 con `{"mensaje": "Sesión iniciada", "debe_cambiar_password": false, "expira_en_segundos": 1800}`
- **AND** el cuerpo no contiene el valor de la cookie `access_token`

#### Scenario: Usuario con cambio de contraseña pendiente
- **WHEN** inicia sesión un usuario con `debe_cambiar_password = true`
- **THEN** la respuesta es 200 con `"debe_cambiar_password": true` y la cookie se emite igual
