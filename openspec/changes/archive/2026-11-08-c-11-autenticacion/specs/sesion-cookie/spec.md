# Spec Delta

## Purpose

Define la sesión del usuario: un token firmado que viaja solo en la cookie `access_token`, cómo se identifica al usuario actual en cada petición, el cierre de sesión y la consulta `GET /auth/yo`.

## ADDED Requirements

### Requirement: Token firmado con sujeto, vencimiento y roles
Al iniciar sesión el sistema SHALL emitir un token JWT firmado con la clave `JWT_SECRET_KEY` y el algoritmo `JWT_ALGORITMO` (HS256 por defecto), con `sub` (id del usuario), `iat`, `exp` = emisión + `ACCESS_TOKEN_MINUTES` y `roles` = roles vigentes del usuario al emitirlo. Los roles del token SHALL ser solo informativos.

#### Scenario: Contenido del token
- **WHEN** un usuario con rol vigente `CLIENTE` inicia sesión y se decodifica la cookie con la clave de firma
- **THEN** el token tiene `sub` igual a su id, `roles = ["CLIENTE"]` y `exp - iat = 1800` con `ACCESS_TOKEN_MINUTES=30`

### Requirement: Token transportado solo en la cookie access_token
El token SHALL viajar únicamente en la cookie `access_token` con `HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` igual a la duración del token en segundos y `Secure` solo si `COOKIE_SECURE` es verdadero. El sistema NO SHALL incluir el token en ningún cuerpo de respuesta ni leerlo de la cabecera `Authorization`.

#### Scenario: Atributos de la cookie
- **WHEN** un login responde 200 con `COOKIE_SECURE=false`
- **THEN** `Set-Cookie` trae `access_token=<token>; HttpOnly; Max-Age=1800; Path=/; SameSite=lax` y no trae `Secure`

#### Scenario: Secure configurable
- **WHEN** la aplicación corre con `COOKIE_SECURE=true` y un login responde 200
- **THEN** `Set-Cookie` incluye además `Secure`

#### Scenario: Token en Authorization ignorado
- **WHEN** se envía `GET /auth/yo` sin cookie y con `Authorization: Bearer <token válido>`
- **THEN** la respuesta es 401

### Requirement: Usuario actual identificado por la cookie con 401
Toda ruta que requiera sesión SHALL identificar al usuario a partir de la cookie `access_token` y SHALL responder 401 con un mensaje propio cuando falte la cookie, el token tenga firma inválida, esté mal formado o vencido, o el usuario no exista o esté inactivo. La identificación SHALL usar la misma conexión de la base que el resto de la petición.

#### Scenario: Sin cookie
- **WHEN** se envía `GET /auth/yo` sin cookie
- **THEN** la respuesta es 401 con `{"detail": "No hay una sesión válida"}`

#### Scenario: Token manipulado
- **WHEN** se envía la cookie con el token alterado en un carácter de la firma
- **THEN** la respuesta es 401

#### Scenario: Token vencido
- **WHEN** se envía una cookie cuyo `exp` ya pasó
- **THEN** la respuesta es 401

#### Scenario: Usuario desactivado con sesión abierta
- **WHEN** un usuario inicia sesión, luego se le pone `activo = false` en la base y envía `GET /auth/yo` con la misma cookie
- **THEN** la respuesta es 401

### Requirement: Cierre de sesión que borra la cookie
`POST /auth/logout` SHALL responder 200 con `{"mensaje": "Sesión cerrada"}` y una cabecera `Set-Cookie` que borra `access_token` (valor vacío, `Max-Age=0`, mismos `Path`, `HttpOnly` y `SameSite`). No SHALL exigir una sesión válida.

#### Scenario: Logout con sesión
- **WHEN** un usuario con sesión envía `POST /auth/logout`
- **THEN** la respuesta es 200 y el `Set-Cookie` borra `access_token`
- **AND** un `GET /auth/yo` posterior sin cookie responde 401

#### Scenario: Logout sin sesión
- **WHEN** se envía `POST /auth/logout` sin cookie
- **THEN** la respuesta es 200

### Requirement: GET /auth/yo con roles vigentes y roles del token
`GET /auth/yo` SHALL devolver al usuario autenticado con `id`, `email`, `nombre`, `debe_cambiar_password`, `roles_vigentes` (leídos de la base en esa petición: no revocados y sin vencer) y `roles_token` (los del token), sin `password_hash`.

#### Scenario: Usuario recién registrado
- **WHEN** `lucas@example.com` inicia sesión y envía `GET /auth/yo`
- **THEN** la respuesta es 200 con `"roles_vigentes": ["CLIENTE"]` y `"roles_token": ["CLIENTE"]` y sin `password_hash`

#### Scenario: Rol revocado después del login
- **WHEN** después del login se escribe `revocada_en` en la asignación `CLIENTE` del usuario y se envía `GET /auth/yo` con la misma cookie
- **THEN** la respuesta es 200 con `"roles_vigentes": []` y `"roles_token": ["CLIENTE"]`

#### Scenario: Rol vencido
- **WHEN** el usuario tiene una asignación abierta con `vence_en` en el pasado
- **THEN** ese rol no aparece en `roles_vigentes`
