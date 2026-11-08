# Spec Delta

## Purpose

Define cómo el sistema guarda y verifica las contraseñas: con bcrypt, con un costo configurable, sin bloquear el servidor y sin que una contraseña larga termine en un error interno.

## ADDED Requirements

### Requirement: Contraseñas guardadas solo como hash bcrypt
El sistema SHALL guardar de cada usuario únicamente el hash bcrypt de su contraseña, calculado con el costo de la variable `BCRYPT_COST`, y NO SHALL guardar ni devolver la contraseña en claro ni el hash en ninguna respuesta.

#### Scenario: Hash con el costo configurado
- **WHEN** se registra un usuario con `BCRYPT_COST=12`
- **THEN** `usuario.password_hash` empieza con `$2b$12$` y no contiene la contraseña enviada

#### Scenario: Costo cambiado por configuración
- **WHEN** la aplicación arranca con `BCRYPT_COST=10` y se registra un usuario
- **THEN** su `password_hash` empieza con `$2b$10$`, sin cambiar el código

### Requirement: Límite de 72 bytes en todo campo que termina en bcrypt
El sistema SHALL rechazar con 422, desde el contrato de entrada, cualquier contraseña de más de 72 bytes en UTF-8 en el registro, en el login y en la actual y la nueva del cambio de contraseña. El límite SHALL medirse en bytes y no en caracteres. Ninguno de esos casos SHALL terminar en 500.

#### Scenario: Contraseña de 73 bytes en el registro
- **WHEN** se envía `POST /auth/registro` con una contraseña de 73 caracteres ASCII
- **THEN** la respuesta es 422 y no se crea ninguna fila

#### Scenario: Caracteres de dos bytes
- **WHEN** se envía `POST /auth/login` con una contraseña de 37 letras «ñ» (37 caracteres, 74 bytes)
- **THEN** la respuesta es 422

#### Scenario: Exactamente 72 bytes
- **WHEN** se registra un usuario con una contraseña de 36 letras «ñ» (72 bytes)
- **THEN** el registro responde 201 y esa misma contraseña sirve para iniciar sesión

#### Scenario: Contraseña actual larga en el cambio
- **WHEN** un usuario autenticado envía `POST /auth/cambiar-password` con una contraseña actual de 80 bytes
- **THEN** la respuesta es 422

### Requirement: bcrypt sin bloquear el servidor y con concurrencia limitada
Toda operación bcrypt (calcular o verificar) SHALL ejecutarse fuera del bucle de eventos y bajo un limitador que permita como máximo `BCRYPT_CONCURRENCIA` operaciones simultáneas. Mientras una petición espera bcrypt, el servidor SHALL seguir atendiendo otras peticiones.

#### Scenario: El servidor responde durante un login
- **WHEN** se envían a la vez un `POST /auth/login` y un `GET /health/live`
- **THEN** `GET /health/live` responde 200 sin esperar a que termine el login

#### Scenario: Concurrencia acotada
- **WHEN** llegan más logins simultáneos que el valor de `BCRYPT_CONCURRENCIA`
- **THEN** a lo sumo `BCRYPT_CONCURRENCIA` cálculos bcrypt corren a la vez y el resto espera su turno sin error

### Requirement: Hash calculado fuera de la transacción
El sistema SHALL calcular el hash de una contraseña nueva y verificar una contraseña existente sin tener abierta la transacción de escritura que la usa, de modo que ninguna conexión de la base quede tomada durante el cálculo.

#### Scenario: Hash antes de abrir la transacción del registro
- **WHEN** se procesa un `POST /auth/registro`
- **THEN** el hash se calcula antes de que se abra la transacción que inserta usuario, rol y cliente

### Requirement: Las respuestas 422 no devuelven el valor enviado
Toda respuesta 422 de validación del sistema SHALL conservar `type`, `loc` y `msg` de cada error y NO SHALL incluir la clave `input` ni el valor enviado por el cliente, de modo que una contraseña rechazada no vuelva en el cuerpo de la respuesta.

#### Scenario: Contraseña de 73 bytes en el registro
- **WHEN** se envía `POST /auth/registro` con una contraseña de 73 caracteres ASCII
- **THEN** la respuesta es 422, ningún elemento de `detail` tiene la clave `input` y el cuerpo no contiene el texto de la contraseña

#### Scenario: Contraseña de 74 bytes en el login
- **WHEN** se envía `POST /auth/login` con una contraseña de 37 letras «ñ»
- **THEN** la respuesta es 422, el cuerpo no tiene la clave `input` ni contiene esas letras
