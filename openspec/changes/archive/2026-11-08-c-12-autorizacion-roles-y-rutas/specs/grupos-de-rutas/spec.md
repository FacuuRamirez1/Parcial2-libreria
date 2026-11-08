# Spec Delta

## Purpose

Define los dos grupos de rutas de la API (abierto y protegido) y el control del cambio obligatorio de contraseña que el grupo protegido aplica a todas sus rutas.

## ADDED Requirements

### Requirement: Grupo abierto sin sesión
Las rutas del grupo abierto (`/health/*`, `/auth/*` y las lecturas públicas del catálogo de `matriz-permisos`) NO SHALL exigir sesión por pertenecer al grupo; dentro de `/auth`, solo `GET /auth/yo` y `POST /auth/cambiar-password` exigen sesión (401), como ya definen `sesion-cookie` y `cambio-password`.

#### Scenario: Catálogo sin sesión
- **WHEN** se envía `GET /libros/` sin cookie
- **THEN** la respuesta es 200 con el envoltorio del listado

#### Scenario: Salud sin sesión
- **WHEN** se envía `GET /health/live` sin cookie
- **THEN** la respuesta es 200

#### Scenario: Login sin sesión
- **WHEN** se envía `POST /auth/login` sin cookie con credenciales válidas
- **THEN** la respuesta es 200 con `Set-Cookie`

### Requirement: Grupo protegido con 401 sin sesión
Toda ruta del grupo protegido SHALL responder 401 con `{"detail": "No hay una sesión válida"}` cuando falta la cookie, el token es inválido o vencido, o el usuario no existe o está inactivo, antes de validar su cuerpo o sus parámetros.

#### Scenario: Ruta protegida sin cookie
- **WHEN** se envía `GET /clientes/1` sin cookie
- **THEN** la respuesta es 401

#### Scenario: Parámetro inválido sin sesión
- **WHEN** se envía `GET /clientes/abc` sin cookie
- **THEN** la respuesta es 401 (no 422)

#### Scenario: Parámetro inválido con sesión
- **WHEN** un vendedor con sesión envía `GET /clientes/abc`
- **THEN** la respuesta es 422 sin ejecutar el handler (caso C-01 de la consigna)

### Requirement: Cambio de contraseña pendiente bloquea el grupo protegido
Mientras un usuario tenga `debe_cambiar_password = true`, toda ruta del grupo protegido SHALL responderle 403 con `{"detail": "Tenés que cambiar la contraseña antes de seguir"}`, tenga o no el rol que la ruta exige (RN-06). Las rutas de `/auth` y las que no piden sesión SHALL seguir disponibles.

#### Scenario: Personal nuevo bloqueado
- **WHEN** `nuevo@example.com` (VENDEDOR, con el cambio pendiente) inicia sesión y envía `POST /ventas/` con un cuerpo válido
- **THEN** la respuesta es 403 con ese mensaje y no se crea ninguna venta

#### Scenario: Administrador con el cambio pendiente
- **WHEN** un usuario con rol vigente `ADMIN` y `debe_cambiar_password = true` envía `GET /eventos`
- **THEN** la respuesta es 403

#### Scenario: Rutas de /auth disponibles con el cambio pendiente
- **WHEN** ese mismo usuario envía `GET /auth/yo` y `POST /auth/logout`
- **THEN** las respuestas son 200, y `GET /auth/yo` muestra `"debe_cambiar_password": true`

#### Scenario: Catálogo disponible con el cambio pendiente
- **WHEN** ese mismo usuario envía `GET /libros/` con su cookie
- **THEN** la respuesta es 200

### Requirement: La misma cookie sirve después del cambio obligatorio
Después de un `POST /auth/cambiar-password` exitoso, la **misma** cookie SHALL dar acceso a las rutas protegidas que el rol del usuario permite, sin iniciar sesión de nuevo, porque el control lee `debe_cambiar_password` de la base en cada petición.

#### Scenario: Desbloqueo sin nuevo login
- **WHEN** `nuevo@example.com` recibe 403 en `POST /ventas/`, cambia su contraseña con éxito y repite `POST /ventas/` con la misma cookie
- **THEN** la repetición responde 201
- **AND** en la base su `debe_cambiar_password` es `false` (caso C-09 de la consigna)

### Requirement: Control del cambio obligatorio montado una sola vez
El control del cambio obligatorio de contraseña SHALL declararse una única vez, sobre el grupo protegido completo, y NO SHALL repetirse en rutas ni en módulos individuales; ninguna ruta del grupo protegido SHALL quedar fuera de él. Toda ruta de la API SHALL pertenecer a exactamente uno de los dos grupos.

#### Scenario: Una sola declaración
- **WHEN** se revisa el código de la aplicación
- **THEN** el control del cambio obligatorio aparece declarado en un único lugar, la definición del grupo protegido

#### Scenario: Ruta nueva protegida por defecto
- **WHEN** se agrega una ruta al grupo protegido sin declarar ninguna dependencia de seguridad propia
- **THEN** esa ruta responde 401 sin sesión y 403 con el cambio de contraseña pendiente

#### Scenario: Inventario de grupos
- **WHEN** se listan las rutas registradas de la aplicación
- **THEN** cada una figura en el grupo abierto o en el protegido según `matriz-permisos`, y ninguna en los dos
