# Spec Delta

## Purpose

Define el límite de intentos fallidos del login por correo y dirección, y el registro de cada intento en `intento_acceso`, que debe sobrevivir aunque la petición que lo originó falle.

## ADDED Requirements

### Requirement: Límite de 5 fallos por correo e IP en 60 segundos
Cuando existan 5 o más intentos fallidos del mismo correo desde la misma IP en los últimos 60 segundos, posteriores al último intento exitoso de ese correo e IP, el login SHALL responder 429 con la cabecera `Retry-After` (segundos enteros, al menos 1) y un mensaje propio, sin buscar al usuario ni calcular ningún hash (RN-07). La IP SHALL ser la dirección del cliente de la conexión.

#### Scenario: El sexto intento fallido seguido
- **WHEN** se envían seis logins seguidos de `lucas@example.com` con contraseña equivocada desde la misma IP
- **THEN** los cinco primeros responden 401 y el sexto responde 429 con `Retry-After` y `{"detail": "Demasiados intentos fallidos; probá de nuevo más tarde"}`
- **AND** el sexto responde en pocos milisegundos (sin verificación bcrypt)

#### Scenario: Retry-After hasta que sale el fallo más viejo
- **WHEN** el login responde 429
- **THEN** `Retry-After` vale los segundos que faltan para que el fallo más antiguo de la ventana cumpla 60 segundos, redondeados hacia arriba y nunca menos de 1

#### Scenario: El límite es por correo
- **WHEN** `lucas@example.com` tiene 5 fallos recientes desde una IP y desde esa misma IP se intenta `ana@example.com`
- **THEN** el login de `ana@example.com` no responde 429 por esos fallos

#### Scenario: La ventana vence
- **WHEN** pasaron más de 60 segundos desde el quinto fallo
- **THEN** un nuevo login con la contraseña correcta responde 200

### Requirement: Un login correcto reinicia la cuenta
Un login exitoso SHALL hacer que los fallos anteriores de ese correo e IP dejen de contar para el límite, sin borrarlos de `intento_acceso`.

#### Scenario: Cuatro fallos, un éxito y otro fallo
- **WHEN** hay 4 fallos recientes, luego un login correcto y luego otro fallo, todo dentro de 60 segundos
- **THEN** ese último fallo responde 401 (no 429)
- **AND** `intento_acceso` conserva las 6 filas

### Requirement: Cada intento verificado queda en intento_acceso
Cada login que llega a la verificación de la contraseña, correcto o fallido y exista o no el correo, SHALL dejar una fila en `intento_acceso` con el correo normalizado, la IP, `exito` y la fecha. Un login rechazado por el límite (429) o por el contrato (422) NO SHALL dejar fila.

#### Scenario: Los cinco fallos están en la tabla
- **WHEN** se ejecutan los seis logins fallidos del escenario del límite
- **THEN** `intento_acceso` tiene exactamente 5 filas nuevas con ese correo, esa IP y `exito = false`

#### Scenario: Correo inexistente también se anota
- **WHEN** se intenta el login de `nadie@example.com`
- **THEN** queda una fila con `email = 'nadie@example.com'` y `exito = false`

#### Scenario: Login correcto anotado
- **WHEN** un login responde 200
- **THEN** queda una fila con ese correo y `exito = true`

### Requirement: El intento se guarda en una transacción propia, siempre confirmada
La escritura en `intento_acceso` SHALL hacerse en una sesión y una transacción propias, distintas de las de la petición, y SHALL confirmarse siempre, aunque la petición termine en error o su transacción se revierta. Es la única escritura del sistema que no comparte la transacción de su petición.

#### Scenario: El fallo sobrevive al rechazo de la petición
- **WHEN** un login fallido termina en 401
- **THEN** la fila del intento queda confirmada y visible desde otra conexión (por ejemplo `psql`) inmediatamente después de la respuesta
