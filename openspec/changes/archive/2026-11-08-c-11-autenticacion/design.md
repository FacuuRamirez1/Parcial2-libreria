# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: specs `hash-contrasenas`, `registro-usuarios`, `login-credenciales`, `limite-intentos-login`, `sesion-cookie`, `cambio-password` y el delta de `app-lifecycle`.

Estado observado en el código (no se rehace):

- `app/core/config.py` (C-08): `Settings` ya tiene `JWT_SECRET_KEY` (sin default), `BCRYPT_COST=12`, `COOKIE_SECURE=False`, `ACCESS_TOKEN_MINUTES=30`, `DB_POOL_SIZE`. **No** tiene tamaño del semáforo ni algoritmo del token.
- `app/main.py` (C-08): el `lifespan` crea `Settings()` como variable local, guarda `engine`, `session_factory` y `hash_ficticio` (bytes) en `app.state`. **No** guarda `settings` ni crea semáforo; el hash ficticio se calcula con `to_thread` sin semáforo (una sola vez al arrancar: aceptable).
- `app/core/security.py` (C-08): solo `calcular_hash_ficticio(costo)`; su docstring ya anuncia que C-11 lo amplía.
- `app/core/unit_of_work.py`: `UnitOfWork` confirma al salir, revierte ante excepción, no cierra la sesión. `get_session` usa `expire_on_commit=False`.
- `app/modules/usuarios/models.py` (C-10): `Usuario`, `AsignacionRol` (índice único parcial de asignación abierta), `IntentoAcceso` (índice `(email, ip, cuando)`, `cuando` con `default_factory` en UTC), `EventoSeguridad`. Relaciones con `lazy="raise"`.
- `app/modules/clientes/`: `Cliente.usuario_id` (UNIQUE, nulo); `ClienteRepository(session)` con `add` por `flush`. `ClienteCreate` no acepta `usuario_id` (y no debe).
- `app/core/errors.py`: manejador global de `IntegrityError` → 409 genérico (red de seguridad; los servicios traducen antes con mensaje propio).
- `requirements.txt`: tiene `bcrypt==4.2.0`; **falta PyJWT**. bcrypt 4.x trunca en silencio más allá de 72 bytes (la 5.x lanza excepción): el límite en el contrato es obligatorio igual.
- Pruebas: no hay runner de Python; se prueba con `test/*.http` (REST Client) con la respuesta esperada comentada y con `psql`.

## Goals / Non-Goals

**Goals:**
- Autenticación completa del Ejercicio 4 y la parte `intento_acceso` del Ejercicio 7, sin conexiones tomadas durante bcrypt y sin bloquear el bucle.
- Dejar la dependencia del usuario actual (401) lista para que C-12 le agregue `requiere_rol`, el control del cambio obligatorio y los dos grupos de rutas sin rehacerla.

**Non-Goals:**
- `requiere_rol`, control de `debe_cambiar_password` (403), grupos abierto/protegido, alta de personal, roles y `/eventos` → C-12.
- Proteger las rutas de dominio existentes → C-12 (hasta entonces siguen abiertas).
- Usuarios del seed (`admin@example.com`, etc.) → C-14. Las pruebas de C-11 crean sus propios usuarios por registro.
- Concurrencia entre peticiones (dos cambios de contraseña simultáneos, carreras del contador de intentos) → cap. 7, fuera de alcance.
- Lista negra de tokens o invalidación de sesiones → la consigna la excluye (DD-11).

## Decisions

### D-01 — Dónde vive cada pieza
`app/core/security.py`: hash, verificación, emisión y decodificación del JWT (funciones puras + `to_thread`). `app/core/dependencies.py` (nuevo): `get_usuario_actual` y el acceso a `settings`/semáforo desde `request.app.state`. Así lo reparte la tabla de estructura de la consigna ("security.py: hash con bcrypt fuera del bucle, y emisión y verificación del token"; "dependencies.py: usuario actual, roles vigentes, control del cambio obligatorio y requiere_rol"). El módulo `usuarios` lleva sus seis archivos con prefijo `/auth` en el router.
*Alternativa*: poner todo en `usuarios/service.py` → descartada: C-12 necesita el usuario actual desde todos los routers.

### D-02 — bcrypt fuera del bucle y bajo semáforo
`hashear_password(password: str, costo: int, semaforo) -> str` y `verificar_password(password: str, hash: str | bytes, semaforo) -> bool`, ambas `async with semaforo: return await asyncio.to_thread(...)`. El semáforo (`asyncio.Semaphore(settings.BCRYPT_CONCURRENCIA)`) se crea en el `lifespan` y se guarda en `app.state.semaforo_bcrypt` (nunca al importar: un `Semaphore` creado antes del bucle es justo el error que la consigna describe en la sección 1.9). El hash se guarda como `str` (`decode("ascii")`). `BCRYPT_CONCURRENCIA=4` por defecto (SU-09): con costo 12 (~300 ms) deja atender ~13 logins/s sin agotar el pool de hilos por defecto.
*Alternativa*: `run_in_executor` con un pool propio → más código y la consigna nombra `to_thread`.

### D-03 — Límite de 72 bytes en el contrato
Un tipo anotado reutilizable en `usuarios/schemas.py`: `Annotated[str, Field(min_length=..), AfterValidator(_max_72_bytes)]` que mide `len(v.encode("utf-8"))` y lanza `ValueError` → 422 de FastAPI. Se usa en `RegistroIn.password` (mín. 8), `LoginIn.password` (mín. 1), `CambioPasswordIn.password_actual` (mín. 1) y `password_nueva` (mín. 8). `max_length` de Pydantic **no** sirve porque cuenta caracteres. Todos los contratos de entrada con `extra="forbid"`.

### D-04 — Correo: normalización y validación sin dependencia nueva
Tipo anotado `CorreoNormalizado`: `BeforeValidator(lambda v: v.strip().lower())` + `max_length=254` + patrón `^[^@\s]+@[^@\s]+\.[^@\s]+$`. Se usa en registro y login (la normalización tiene que ser la misma en los dos, y también es la que se guarda en `intento_acceso`).
*Alternativa*: `EmailStr` → requiere `email-validator` y su política de dominios especiales puede rechazar correos de prueba; además no pasa a minúsculas la parte local. Se descarta para no sumar comportamiento opaco. La unicidad sigue en la base (`uq_usuario_email`, `uq_cliente_email`), que compara texto exacto: por eso la normalización es obligatoria.

### D-05 — Registro en un solo bloque (RN-02)
1. Fuera de la transacción: `hash = await hashear_password(...)`.
2. `async with uow:` → `usuario = Usuario(...)`; `await uow.usuarios.add(usuario)` (flush: obtiene `id` y dispara `uq_usuario_email`); `await uow.asignaciones.add(AsignacionRol(usuario_id=usuario.id, rol="CLIENTE"))`; `cliente = Cliente(nombre, email, usuario_id=usuario.id)`; `await uow.clientes.add(cliente)` (flush: dispara `uq_cliente_email`).
3. `except IntegrityError` alrededor del `async with` (el UoW ya revirtió): SQLSTATE `23505` → 409 `"El correo ya está registrado"` (mismo mensaje para usuario o cliente: no revela cuál existe); otro SQLSTATE → se relanza al manejador global.
`UsuariosUnitOfWork` compone `usuarios`, `asignaciones`, `eventos` y `clientes` (`ClienteRepository` importado del módulo clientes) sobre la misma sesión. No hay consulta previa del correo. No se escribe `evento_seguridad` (RN-16 no lista el auto-registro). Respuesta `RegistroOut {id, email, nombre, cliente_id}`, sin cookie (SU-10).

### D-06 — Login: orden y fronteras de transacción
1. **Bloque de lectura** (`async with uow:`): una sola consulta `contar_fallos_recientes(email, ip, desde=ahora-60s)` que devuelve `(cantidad, mas_antiguo)` sobre `intento_acceso` con `exito = false`, `cuando > desde` y `cuando >` (subconsulta: último `exito = true` del mismo correo e IP, o `-infinity`). Si `cantidad >= 5` → `HTTPException(429, headers={"Retry-After": str(max(1, ceil(60 - (ahora - mas_antiguo))))})`, sin tocar `usuario` ni bcrypt. Si no, en el mismo bloque: `usuario = get_by_email(email)` y, si existe, `roles = roles_vigentes(usuario.id)`. Al salir, el UoW confirma una transacción de solo lectura y **la conexión vuelve al pool antes de bcrypt**.
2. **Fuera de transacción**: `ok = await verificar_password(password, usuario.password_hash if usuario else app.state.hash_ficticio, semaforo)`. `exito = usuario is not None and usuario.activo and ok`. El usuario inactivo se verifica igual (mismo tiempo) y da 401.
3. **Intento** (D-07): `await registro_intentos.anotar(email, ip, exito)`, siempre, antes de responder.
4. `exito` falso → 401 `"Correo o contraseña incorrectos"`. Verdadero → token (D-08), `set_cookie` y `LoginOut {mensaje, debe_cambiar_password, expira_en_segundos}`.
Las fechas de la ventana y de `intento_acceso.cuando` salen ambas del reloj de la aplicación en UTC (el `default_factory` del modelo), para que la comparación sea coherente. El 429 y el 422 no se anotan: si el 429 se anotara como fallo, la ventana nunca terminaría de vaciarse mientras el atacante insiste, y la consigna pide que "los cinco fallos" estén en la tabla.
*Alternativa*: contar con `count(*)` y luego otra consulta para el más viejo → la consigna dice que el límite "cuesta una consulta".

### D-07 — `intento_acceso` en sesión y transacción propias (DD-14)
`RegistroIntentosPropio` en `usuarios/repository.py`, construido por una dependencia del router a partir de `request.app.state.session_factory`. Su método `anotar` hace `async with fabrica() as sesion: async with sesion.begin(): sesion.add(IntentoAcceso(...))`. Lleva el comentario obligatorio:
- **Qué hace distinto**: abre su propia sesión y su propia transacción, y confirma siempre; es la única escritura del sistema que no usa el Unit of Work de la petición.
- **Por qué no puede compartirla**: el fallo que se quiere contar es el mismo que revierte la transacción de la petición; si compartiera la transacción, el intento fallido desaparecería con el rollback y el límite nunca se alcanzaría.
- **Costo**: deja filas aunque la petición falle, y toma una segunda conexión del pool durante el login.
El servicio recibe `registro_intentos` ya construido (no construye sesiones ni UoW). El lector del contador (paso 1 de D-06) sí usa la sesión de la petición: es lectura.

### D-08 — Token y cookie
PyJWT (`PyJWT==2.10.1`, cumple "≥ 2.8"): `jwt.encode({"sub": str(usuario.id), "iat": ahora, "exp": ahora + ACCESS_TOKEN_MINUTES, "roles": sorted(roles)}, JWT_SECRET_KEY, algorithm=JWT_ALGORITMO)`. `sub` como **string** (PyJWT 2.10 valida que lo sea). Decodificación con `algorithms=[JWT_ALGORITMO]` (lista fija: nunca se acepta el `alg` que trae el token) y `options={"require": ["sub", "exp", "iat"]}`; cualquier `jwt.InvalidTokenError` (incluye vencido y firma mala) o `sub` no entero → 401.
Cookie con `response.set_cookie("access_token", token, max_age=segundos, httponly=True, samesite="lax", secure=settings.COOKIE_SECURE, path="/")`; logout con `response.delete_cookie("access_token", path="/", httponly=True, samesite="lax", secure=settings.COOKIE_SECURE)`. `JWT_ALGORITMO="HS256"` y `BCRYPT_CONCURRENCIA=4` se agregan a `Settings` con default (no son secretos; SU-08/SU-09).

### D-09 — Usuario actual (adelanto mínimo de C-12)
`get_usuario_actual(request: Request, session: SessionDep) -> UsuarioActual` en `app/core/dependencies.py`: lee **solo** `request.cookies.get("access_token")`, decodifica, `await session.get(Usuario, int(sub))`, exige `activo`; si algo falla → 401 `"No hay una sesión válida"`. Devuelve `UsuarioActual(usuario, roles_token)` (dataclass). Recibe `SessionDep`, que FastAPI cachea por petición: el `UsuariosUnitOfWork` de la misma ruta recibe **la misma sesión** (una conexión por petición autenticada). C-12 agrega en este archivo `requiere_rol` y el control de cambio obligatorio sin tocar esta función.

### D-10 — `GET /auth/yo` y roles vigentes
`AsignacionRolRepository.roles_vigentes(usuario_id)`: `select(AsignacionRol.rol).where(usuario_id == :id, revocada_en IS NULL, or_(vence_en IS NULL, vence_en > now))` ordenado. Lo usan el login (roles del token) y `/auth/yo` (C-12 lo reutiliza en `requiere_rol`). `YoOut {id, email, nombre, debe_cambiar_password, roles_vigentes, roles_token}`.

### D-11 — Cambio de contraseña en dos bloques
1. `async with uow:` relee al usuario por id (cierra además la transacción implícita que abrió `get_usuario_actual`, devolviendo la conexión antes de bcrypt).
2. Fuera de transacción: `verificar_password(actual, usuario.password_hash)`; si falla → 422 `"La contraseña actual no es correcta"`. `nuevo_hash = hashear_password(nueva)`.
3. `async with uow:` `usuario.password_hash = nuevo_hash; usuario.debe_cambiar_password = False; await uow.usuarios.update(usuario); await uow.eventos.add(EventoSeguridad(actor=usuario.email, accion="Cambio de contraseña"))` (RN-16, mismo bloque). 200 `{"mensaje": "Contraseña actualizada"}`, sin `Set-Cookie`.
Por qué 422 y no 401 para la actual incorrecta: ver supuesto S-01.

### D-12 — Dirección del cliente
`request.client.host` (SU-09), o `"desconocida"` si no hay cliente; recortada a 45 caracteres (largo de `intento_acceso.ip`). No se lee `X-Forwarded-For` (falsificable sin un proxy de confianza configurado; el despliegue del parcial no es este proyecto).

### D-13 — Pruebas (equivalente RED/GREEN sin runner)
`test/C-11-autenticacion.http` se escribe **antes** del código de cada grupo (RED: las rutas no existen → 404/405), y se completa caso por caso hasta que cada respuesta coincide con su comentario (GREEN). Las sesiones se manejan como pide la consigna: `# @name login…`, `# @no-cookie-jar` y `Cookie: {{loginX.response.headers.Set-Cookie}}`. Los efectos en la base (filas sueltas, `intento_acceso`, `evento_seguridad`, `password_hash`) se verifican con consultas `psql` anotadas en el mismo archivo como comentarios. El tiempo parecido de C-04 y el "pocos milisegundos" de C-05 se miden con el tiempo que muestra REST Client (o `curl -w "%{time_total}"`). Correos únicos por corrida: `{{$timestamp}}` en el correo de registro para no depender del seed.

### D-14 — Los 422 no devuelven el valor enviado
El cuerpo 422 por defecto de FastAPI incluye `input` con el valor que el cliente mandó; en `/auth/registro`, `/auth/login` y `/auth/cambiar-password` eso devolvería la contraseña (p. ej. la de 73 bytes) en la respuesta, y quedaría en logs de proxies y consolas del cliente. Se registra en `app/core/errors.py` (`init_error_handlers`, mismo patrón que los manejadores de `IntegrityError`/`DataError`) un manejador de `RequestValidationError` que devuelve 422 con `{"detail": [...]}` igual que el de FastAPI pero sin `input`; conserva `type`, `loc`, `msg` y `ctx` (con sus valores pasados a texto si no son serializables: p. ej. el `ValueError` de un validador). Vale para **todas** las rutas, no solo `/auth`: es la misma fuga en cualquier entrada y un solo punto es más simple y más seguro que filtrar por ruta.
*Alternativa*: quitar `input` solo de los campos de contraseña → descartada: exige conocer el `loc` de cada campo sensible y deja pasar un `input` de un objeto entero (p. ej. un error de modelo que contenga el cuerpo completo).

### Supuestos (ambigüedades de la consigna, a confirmar)
- **S-01** Contraseña actual incorrecta en el cambio → **422** (la tabla solo da 200/401/422 y la KB reserva 401 para "sin sesión"; un 401 haría que un cliente crea que perdió la sesión).
- **S-02** `get_usuario_actual` se adelanta de C-12 a C-11 (solo la parte 401) porque `GET /auth/yo` y `POST /auth/cambiar-password` lo necesitan; `CHANGES.md` lo ubica en C-12.
- **S-03** `POST /auth/logout` no exige sesión y responde 200 siempre (la fila reconstruida de la tabla dice "Cualquiera, 200"; IN-03 lo marcaba incierto).
- **S-04** El 429 y el 422 del login no se anotan en `intento_acceso`; sí se anotan los correos inexistentes.
- **S-05** "Desde el último éxito" se mide por el mismo correo **e IP**.
- **S-06** `Retry-After` = segundos hasta que el fallo más antiguo de la ventana cumpla 60 s.
- **S-07** Largo mínimo de contraseña: 8 en registro y en la nueva del cambio; 1 en login y en la actual (para no bloquear contraseñas viejas o del seed). SU-09.
- **S-08** El correo se normaliza a minúsculas y sin espacios; validación por patrón simple, sin `EmailStr`.
- **S-09** El auto-registro no escribe `evento_seguridad` (RN-16 solo nombra alta de personal, cambio de rol y cambio de contraseña).
- **S-10** Forma de las respuestas no fijadas por la consigna: `RegistroOut {id, email, nombre, cliente_id}`, `YoOut` (D-10), mensajes literales de los specs. El cuerpo del login sí es el de la consigna.
- **S-11** Correo repetido: mismo mensaje sea de usuario o de cliente.
- **S-12** `BCRYPT_CONCURRENCIA=4` y `JWT_ALGORITMO=HS256` por defecto.
- **S-13** Hasta C-12, `/auth` se monta con un `include_router` común; el reparto en grupos lo hace C-12.

## Risks / Trade-offs

- [Dos conexiones por login: la de la petición y la de `intento_acceso`] → aceptado por la consigna (es el costo declarado en el comentario); la de la petición se libera antes de bcrypt, así que no se solapan durante el cálculo.
- [Carrera del contador: logins fallidos simultáneos pueden pasar todos el control y dejar más de 5 fallos] → fuera de alcance (cap. 7); `Retry-After` puede quedar corto y el cliente recibe otro 429, sin romper la regla.
- [Diferencia de tiempo residual entre correo inexistente y existente (una consulta de roles menos)] → del orden de 1 ms frente a ~300 ms de bcrypt; el criterio de la consigna es "tiempo parecido".
- [bcrypt 4.2 trunca más allá de 72 bytes en lugar de fallar] → el contrato corta antes; si se actualiza a bcrypt 5, el comportamiento observable no cambia.
- [El correo con mayúsculas guardado por el TP en `cliente`] → los datos del TP y del seed están en minúsculas; si hubiera uno con mayúsculas, el registro con la versión en minúsculas no chocaría con el UNIQUE. Se acepta (el seed de C-14 los carga en minúsculas).
- [El core (`dependencies.py`) importa `app.modules.usuarios.models`] → dependencia de core a un módulo, aceptada porque la consigna ubica ahí el usuario actual; no hay ciclo (los modelos no importan core salvo `metadata`).
- [Rutas de dominio abiertas hasta C-12] → conocido y declarado en la propuesta.

## Migration Plan

- Sin cambios de esquema: no hay migración nueva (0001–0004 intactas).
- Despliegue: `pip install -r requirements.txt` (PyJWT), agregar `BCRYPT_CONCURRENCIA`/`JWT_ALGORITMO` al `.env` si se quieren valores distintos de los por defecto, reiniciar.
- Rollback: revertir el commit; las filas de `usuario`/`intento_acceso` creadas por las pruebas se limpian con el seed.
