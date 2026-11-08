# Proposal

> **Governance: CRÍTICO** (autenticación, contraseñas, token, intentos de acceso). Este change produce solo artefactos de planificación. El `/opsx:apply` requiere **aprobación humana explícita** antes de escribir cualquier línea de código, y tiene puntos de control con aprobación en el código sensible (hash y token, login, `intento_acceso`, registro y cambio de contraseña). Ver `tasks.md`.

## Why

Después de C-08, C-09 y C-10 el proyecto tiene `Settings` con `JWT_SECRET_KEY` sin valor por defecto, el hash ficticio del login calculado en el `lifespan`, los repositorios y Unit of Work por módulo, y las tablas `usuario`, `asignacion_rol`, `intento_acceso` y `evento_seguridad`, pero **nadie puede registrarse ni iniciar sesión**: el módulo `usuarios` solo tiene modelos y no hay bcrypt de verdad, token ni cookie. El Ejercicio 4 del Parcial (14 pts) y la parte `intento_acceso` del Ejercicio 7 piden la autenticación completa (RN-02, RN-07, RN-08, RN-15), y la autorización por roles (C-12) no puede construirse sin un usuario actual leído de la cookie.

## What Changes

- **Contraseñas (`app/core/security.py`)**: hash y verificación con bcrypt **siempre** fuera del bucle (`asyncio.to_thread`) y bajo un semáforo de concurrencia configurable; costo tomado de `BCRYPT_COST`; el hash se calcula antes de abrir la transacción. Todo campo que termina en bcrypt (contraseña del registro, del login, actual y nueva del cambio) acepta como máximo **72 bytes** → 422.
- **Token (`app/core/security.py`)**: JWT HS256 (SU-08) con `sub`, `exp`, `iat` y los roles vigentes al emitirlo; firmado con `JWT_SECRET_KEY`. Viaja solo en la cookie `access_token` (`HttpOnly`, `SameSite=Lax`, `Max-Age` = duración, `Secure` según `COOKIE_SECURE`, `Path=/`); nunca en el cuerpo ni leído de `Authorization` (DD-11).
- **Usuario actual (`app/core/dependencies.py`, nuevo)**: dependencia `get_usuario_actual` que lee `request.cookies["access_token"]` y responde **401** sin cookie, con token inválido o vencido, o con usuario inexistente o inactivo; usa la misma sesión que el Unit of Work. La necesitan `GET /auth/yo` y `POST /auth/cambiar-password`. `requiere_rol`, el control del cambio obligatorio y los dos grupos de rutas siguen siendo C-12.
- **Módulo `usuarios` completo**: `schemas.py`, `repository.py` (usuarios, asignaciones con roles vigentes, intentos, eventos), `unit_of_work.py` (compone también `ClienteRepository` para el registro), `service.py` y `router.py` con prefijo `/auth`.
- **`POST /auth/registro`** (RN-02): crea `usuario` + `asignacion_rol` CLIENTE + `cliente` con `usuario_id` en **un solo** bloque de Unit of Work, sin pre-consultar el correo; correo repetido de usuario o de cliente → **409** con mensaje propio, sin filas sueltas ni apropiarse de la ficha existente; 201 sin `password_hash` y **sin iniciar sesión** (SU-10).
- **`POST /auth/login`** (RN-07, RN-08): 1) límite de intentos (≥ 5 fallos del mismo correo e IP en 60 s desde el último éxito → **429** + `Retry-After`, sin calcular hash); 2) verificación contra el hash del usuario o contra el hash ficticio si el correo no existe (mismo 401, mismo cuerpo, tiempo parecido; usuario inactivo también 401); 3) éxito → `Set-Cookie` y cuerpo `{mensaje, debe_cambiar_password, expira_en_segundos}` sin token.
- **`intento_acceso`**: cada login correcto o fallido (no el 429) se anota en una **sesión y transacción propias**, siempre confirmadas, con el comentario de las tres cosas (qué hace distinto, por qué no comparte la transacción, costo). Un login correcto reinicia la cuenta: los fallos anteriores quedan en la tabla y dejan de contar.
- **`POST /auth/logout`**: borra la cookie (200), no exige sesión. **`GET /auth/yo`**: usuario, roles vigentes leídos de la base y roles del token. **`POST /auth/cambiar-password`**: verifica la actual, guarda la nueva, deja `debe_cambiar_password = false` y una línea en `evento_seguridad` en el mismo bloque (RN-16); sin token nuevo, la misma cookie sigue sirviendo.
- **Configuración**: `Settings` suma `BCRYPT_CONCURRENCIA` (tamaño del semáforo, SU-09) y `JWT_ALGORITMO` (`HS256` por defecto, SU-08); el `lifespan` guarda `settings` y el semáforo en `app.state`. `env.example` documenta las nuevas variables (sin secretos).
- **Dependencias**: se agrega **PyJWT** a `requirements.txt` (hoy falta; bcrypt ya está).
- **Pruebas**: `test/C-11-autenticacion.http` (casos C-02..C-05 de la consigna en su parte de autenticación) y consultas `psql` de verificación.

## Capabilities

### New Capabilities

- `hash-contrasenas`: cómo se guardan y verifican las contraseñas: bcrypt con costo configurable, fuera del bucle y con concurrencia limitada, hash antes de la transacción, límite de 72 bytes en todo campo que termina en bcrypt.
- `registro-usuarios`: auto-registro de un cliente con usuario, rol CLIENTE y ficha de cliente atómicos, unicidad del correo y respuesta sin sesión ni datos sensibles.
- `login-credenciales`: verificación de correo y contraseña en el login con respuesta y tiempo indistinguibles exista o no el correo, y el cuerpo de la respuesta exitosa.
- `limite-intentos-login`: límite de 5 fallos por correo e IP en 60 s con 429 y `Retry-After`, y el registro de cada intento en `intento_acceso` independiente de la petición.
- `sesion-cookie`: token firmado transportado solo en la cookie `access_token`, usuario actual con 401, cierre de sesión y `GET /auth/yo`.
- `cambio-password`: cambio de contraseña del usuario autenticado, con evento de seguridad, sin token nuevo y sin invalidar la sesión.

### Modified Capabilities

- `app-lifecycle`: la estructura de módulos obligatoria suma `usuarios`; el ciclo de vida deja disponibles para las peticiones la configuración, el hash ficticio y el limitador de concurrencia de bcrypt.

## Impact

- **Código nuevo**: `app/core/dependencies.py`; `app/modules/usuarios/{schemas,repository,unit_of_work,service,router}.py`; `test/C-11-autenticacion.http`.
- **Código modificado**: `app/core/security.py` (C-08: suma hash, verificación, semáforo y JWT; conserva `calcular_hash_ficticio`), `app/core/config.py` (C-08: dos campos con valor por defecto no secreto), `app/main.py` (C-08/C-09: `app.state.settings`, `app.state.semaforo_bcrypt`, `include_router` de `/auth`), `requirements.txt` (PyJWT), `env.example`.
- **Usado sin modificar**: `app/modules/clientes/models.py` y `repository.py` (el registro construye `Cliente` con `usuario_id` a través de `ClienteRepository` dentro del UoW de usuarios; `ClienteCreate` no cambia y sigue sin aceptar `usuario_id`), `app/core/unit_of_work.py`, `app/core/repository.py`, modelos de C-10.
- **Intactos**: migraciones (no hay cambios de esquema), routers de dominio (su protección es C-12), `scripts/seed.py` (los usuarios del seed son C-14).
- **API**: 5 endpoints nuevos bajo `/auth`, todos en el grupo abierto según la tabla de la consigna. Ninguna ruta existente cambia.
- **Seguridad**: con este change las rutas del dominio siguen **abiertas**; quedan protegidas en C-12.
