# Design

## Context

Motivación y alcance: ver `proposal.md`. Requisitos: specs `autorizacion-roles`, `grupos-de-rutas`, `matriz-permisos`, `alta-personal`, `administracion-roles` e `historial-seguridad`.

Estado observado en el código (no se rehace):

- `app/core/dependencies.py` (C-11): `get_usuario_actual(request, session: SessionDep) -> UsuarioActual(usuario, roles_token)`; 401 `"No hay una sesión válida"`; lee solo la cookie; `session.get(Usuario, id)` y exige `activo`. Su docstring ya anuncia que C-12 suma `requiere_rol` y el control del cambio obligatorio **sin tocarla**. Se respeta.
- `app/core/database.py`: `SessionDep` = `Depends(get_session)`; FastAPI cachea la dependencia por petición → todas las dependencias y el UoW de una ruta reciben la **misma** `AsyncSession`. `expire_on_commit=False`.
- `app/core/unit_of_work.py`: `UnitOfWork` confirma al salir sin excepción y revierte con excepción; puede abrirse **varias veces** sobre la misma sesión (C-11 ya lo hace en `cambiar_password`).
- `app/modules/usuarios/`: `AsignacionRolRepository.roles_vigentes(usuario_id, ahora)` (D-10 de C-11; una consulta con `revocada_en IS NULL AND (vence_en IS NULL OR vence_en > :ahora)`); `UsuarioRepository.get_by_email`; `EventoSeguridadRepository` sin métodos propios; `UsuariosUnitOfWork` con `usuarios`, `asignaciones`, `intentos`, `eventos`, `clientes`. `schemas.py` ya tiene `CorreoNormalizado` y `PasswordBcrypt` (72 bytes). `service._es_unicidad` reconoce SQLSTATE 23505. El router `/auth` vive en `usuarios/router.py`.
- `app/modules/usuarios/models.py` (C-10): `AsignacionRol` con CHECK de rol, índice único parcial `ix_asignacion_rol_abierta (usuario_id, rol) WHERE revocada_en IS NULL`, `otorgada_por` FK a `usuario` con índice; `EventoSeguridad(cuando, actor texto, accion ≤ 255)`. **Ninguna columna nueva hace falta → sin migración.**
- `app/main.py`: incluye los 8 routers con `include_router` plano, todos abiertos. Ningún router de dominio declara dependencias de seguridad.
- Routers de dominio (C-09): `editoriales`, `generos`, `autores` (POST, GET lista, GET {id}, PATCH, GET {id}/libros), `libros` (POST, GET lista, GET {id}, PATCH; **no hay** `DELETE`, `reponer` ni `movimientos` todavía: son C-13), `clientes` (POST, GET lista, GET {id}, PATCH, POST perfil, GET ventas), `ventas` (POST, GET lista, GET {id}). Cada uno construye su UoW con una dependencia `get_<modulo>_uow(session: SessionDep)`.
- Pruebas: sin runner de Python; `test/*.http` (REST Client) con la respuesta esperada comentada y pasos `psql`. `scripts/seed.py` es idempotente pero **no vacía** tablas ni carga usuarios (los usuarios de la consigna son C-14).

### Tabla de endpoints reconstruida (consigna, págs. 16-18)

La tabla del PDF viene con columnas entrelazadas: la columna "Ruta" está corrida una fila hacia abajo respecto de "Grupo/Método/Códigos". Re-alineando por conteo (9 filas en la pág. 16, 18 en la 17, 4 en la 18; 2 filas "Abierto GET" + 12 "ADMIN" + 4 "VENDEDOR, ADMIN" en la pág. 17) queda:

| Ruta | Grupo | Quién | Códigos |
|---|---|---|---|
| `GET /editoriales`, `/generos` | Abierto | Cualquiera | 200, 422 |
| `GET /editoriales/{id}/libros`, `/generos/{id}/libros`, `/autores/{id}/libros` | **Abierto** | **Cualquiera** | 200, 404 |
| `POST /usuarios` | Protegido | ADMIN | 201, 409, 422 |
| `GET /usuarios/{id}/roles` | Protegido | ADMIN | 200, 404 |
| `POST /usuarios/{id}/roles` | Protegido | ADMIN | 201, 404, 409, 422 |
| `DELETE /usuarios/{id}/roles/{rol}` | Protegido | ADMIN | 200, 404, 409 |
| `GET /eventos` | Protegido | ADMIN | 200, 422 |
| `POST /editoriales`, `/generos`, `/autores` | Protegido | ADMIN | 201, 409, 422 |
| `PATCH /editoriales/{id}`, `/autores/{id}` | Protegido | ADMIN | 200, 404, 409, 422 |
| `POST /libros`, `PATCH /libros/{id}` | Protegido | ADMIN | 201, 409, 422 / 200, 404, 409, 422 |
| `DELETE /libros/{id}`, `reponer`, `movimientos` | Protegido | ADMIN | (C-13) |
| `POST /clientes`, `GET`/`PATCH /clientes/{id}`, `POST …/perfil`, `GET …/ventas` | Protegido | VENDEDOR, ADMIN | 201, 409, 422 / 200, 404, 409, 422 / 201, 404, 409 / 200, 404 |
| `POST /ventas` | Protegido | VENDEDOR, ADMIN | 201, 409, 422 |
| `GET /ventas` (listado) | Protegido | **Solo ADMIN** (S-02, decidido por el usuario) | 200, 403, 422 |
| `GET /ventas/{id}` | Protegido | El personal o el cliente dueño (en C-12 provisorio: VENDEDOR o ADMIN, S-04) | 200, 403, 404 |
| `GET /mis-ventas` | Protegido | Autenticado | 200, 422 (C-13) |

Una diferencia con la KB sale de esta re-alineación (S-01: `…/{id}/libros` abiertas); S-02 (`GET /ventas` solo ADMIN) la decidió el usuario.

## Goals / Non-Goals

**Goals:**
- Autorización del Ejercicio 5 sin una segunda conexión por petición y sin rehacer `get_usuario_actual`.
- Que la protección sea **por defecto**: una ruta agregada al grupo protegido queda cubierta por el 401 y el control del cambio obligatorio sin que nadie lo recuerde.
- Cambios en los routers de dominio limitados a "en qué grupo va cada ruta" y "qué rol exige"; ningún servicio de dominio cambia.

**Non-Goals:**
- Decisión de dueño de `GET /ventas/{id}`, `/mis-ventas`, `DELETE /libros/{id}`, `reponer`, `movimientos`, el `usuario_id` de los movimientos → C-13.
- Seed con los usuarios de la consigna y el evento `SISTEMA` → C-14 (C-12 usa un `.sql` de preparación provisorio).
- Desactivar usuarios o editar personal (no hay ruta en la consigna).
- Concurrencia entre dos administradores que se revocan a la vez (cap. 7).
- Invalidar sesiones al revocar (no hace falta: el permiso se lee de la base).

## Decisions

### D-01 — `requiere_rol(*roles)` como fábrica de dependencias en `app/core/dependencies.py`
```python
def requiere_rol(*roles: str) -> Callable[..., Awaitable[UsuarioActual]]:
    permitidos = frozenset(roles)
    async def _dependencia(actual: UsuarioActualDep, session: SessionDep) -> UsuarioActual:
        vigentes = await AsignacionRolRepository(session).roles_vigentes(actual.usuario.id, datetime.now(UTC))
        if permitidos.isdisjoint(vigentes):
            raise HTTPException(403, "No tenés permiso para esta operación")
        return actual
    return _dependencia
```
- Reusa `roles_vigentes` (misma consulta que login y `/auth/yo`): una sola definición de "vigente".
- Recibe `SessionDep` y `UsuarioActualDep`: FastAPI cachea ambas por petición → misma sesión que el UoW (regla "nunca dos conexiones") y `get_usuario_actual` se ejecuta una sola vez aunque la pidan el control del grupo y `requiere_rol`.
- Devuelve `UsuarioActual`, así la ruta que necesita al actor (alta de personal, roles) lo recibe con `actual: UsuarioActual = Depends(requiere_rol("ADMIN"))` sin otra consulta.
- Constantes `ADMIN`, `VENDEDOR`, `CLIENTE` (y `PERSONAL = ("VENDEDOR", "ADMIN")`) en `dependencies.py` para no repetir literales.
- Se valida al construir que cada rol pedido esté entre los tres válidos (error de programación al importar, no en runtime).
*Alternativa*: leer los roles del JWT → prohibido (RN-04, DD-10). *Alternativa*: `Security`/scopes de FastAPI → agrega OAuth2 y la cabecera `Authorization`, que la consigna excluye.

### D-02 — Control del cambio obligatorio: `exigir_password_al_dia`
```python
async def exigir_password_al_dia(actual: UsuarioActualDep) -> UsuarioActual:
    if actual.usuario.debe_cambiar_password:
        raise HTTPException(403, "Tenés que cambiar la contraseña antes de seguir")
    return actual
```
`debe_cambiar_password` sale del `Usuario` que `get_usuario_actual` acaba de leer de la base en **esta** petición (sesión nueva por petición, sin caché entre peticiones): después del cambio de contraseña la misma cookie ya pasa (spec `grupos-de-rutas`, caso C-09). Orden observable en una ruta protegida: 401 (sin sesión) → 403 cambio pendiente → 403 sin rol → validación de parámetros/cuerpo (422) → handler. FastAPI resuelve las dependencias del router antes que las de la ruta y ambas antes de validar parámetros y cuerpo, y corta en la primera `HTTPException`; por eso `GET /clientes/abc` da 401 sin sesión y 422 con sesión (caso C-01).

### D-03 — Dos grupos de rutas en `app/main.py`, control montado una vez
```python
abierto = APIRouter()
protegido = APIRouter(dependencies=[Depends(exigir_password_al_dia)])  # ÚNICO lugar del control (RN-06)
abierto.include_router(health_router); abierto.include_router(auth_router)
abierto.include_router(editoriales.router_abierto); ...
protegido.include_router(editoriales.router_protegido); ...; protegido.include_router(personal_router); protegido.include_router(eventos_router)
app.include_router(abierto); app.include_router(protegido)
```
Con un comentario que diga por qué son dos grupos: FastAPI **suma** dependencias (router padre + hijo + ruta) y no tiene forma de **restarlas**; si el control colgara de la app o de un router común, `/auth/cambiar-password` (la única salida del bloqueo) también quedaría bloqueada. `exigir_password_al_dia` ya depende de `get_usuario_actual`, así que el grupo protegido da el 401 por sí mismo.
*Alternativa*: dependencia global con lista de rutas exceptuadas → frágil (una ruta nueva olvidada en la lista queda bloqueada o abierta) y contradice "montado una sola vez sobre el grupo".
*Alternativa*: middleware → corre fuera del sistema de dependencias, necesitaría su propia sesión (segunda conexión) y decodificar el token por su cuenta.

### D-04 — Cada `router.py` de dominio expone `router_abierto` y/o `router_protegido`
Mismo prefijo y `tags` en los dos; la dependencia `get_<modulo>_uow` se comparte. Cada ruta pasa al router de su grupo sin cambiar su firma ni su servicio; el rol se declara:
- en el **router protegido del módulo** (`APIRouter(prefix=…, dependencies=[Depends(requiere_rol(*PERSONAL))])`) cuando todas sus rutas comparten el rol (clientes; `/usuarios` y `/eventos` con ADMIN), o
- **en la ruta** (`dependencies=[Depends(requiere_rol(ADMIN))]`, o como parámetro si necesita al actor) cuando el módulo mezcla roles (ventas: `POST /` y `GET /{id}` con PERSONAL, `GET /` con ADMIN).
Nunca en el grupo `protegido` (no todas sus rutas exigen el mismo rol). Mismo camino y método distinto en dos grupos (p. ej. `GET /editoriales/` abierto y `POST /editoriales/` protegido) funciona: el enrutador de Starlette sigue buscando cuando el camino coincide y el método no, y toma la ruta que coincide en ambos. Ningún par (camino, método) se registra dos veces (se verifica listando `app.routes`).
Rutas por grupo (spec `matriz-permisos`):

| Módulo | `router_abierto` | `router_protegido` (rol) |
|---|---|---|
| health | `/live`, `/ready` | — |
| usuarios (`/auth`) | las 5 de C-11 (sin cambios) | — |
| editoriales | `GET /`, `GET /{id}`, `GET /{id}/libros` | `POST /`, `PATCH /{id}` (ADMIN) |
| generos | `GET /`, `GET /{id}`, `GET /{id}/libros` | `POST /`, `PATCH /{id}` (ADMIN) |
| autores | `GET /`, `GET /{id}`, `GET /{id}/libros` | `POST /`, `PATCH /{id}` (ADMIN) |
| libros | `GET /`, `GET /{id}` | `POST /`, `PATCH /{id}` (ADMIN) |
| clientes | — | las 6 (PERSONAL, a nivel de router) |
| ventas | — | `POST /` (PERSONAL), `GET /` (ADMIN, S-02), `GET /{id}` (PERSONAL provisorio, ver S-04) |
| usuarios (`/usuarios`) | — | `POST /`, `GET`/`POST /{id}/roles`, `DELETE /{id}/roles/{rol}` (ADMIN, a nivel de router) |
| usuarios (`/eventos`) | — | `GET /` (ADMIN, a nivel de router) |

### D-05 — Alta de personal (`POST /usuarios`) en dos bloques
Contrato `PersonalIn(email: CorreoNormalizado, nombre, password: PasswordBcrypt ≥ 8, rol: Literal["ADMIN","VENDEDOR"])`, `extra="forbid"`; salida `PersonalOut {id, email, nombre, debe_cambiar_password, roles_vigentes}`.
1. `async with uow: pass` — con un comentario: cierra la transacción implícita que abrieron `get_usuario_actual` y `requiere_rol` y **devuelve la conexión al pool antes de bcrypt** (mismo patrón que `cambiar_password`, D-11 de C-11). Sin esto la conexión quedaría tomada ~300 ms sin usar la base.
2. Fuera de transacción: `hash = await hashear_password(password, BCRYPT_COST, semaforo)`.
3. Un solo bloque: `Usuario(…, debe_cambiar_password=True)` → `add` (flush; 23505 → 409 `"El correo ya está registrado"`, sin pre-consulta) → `AsignacionRol(usuario_id, rol, otorgada_por=actor.id)` → `EventoSeguridad(actor=actor.email, accion=f"Alta de personal {email} con rol {rol}")`. Cualquier fallo revierte las tres.
El correo del actor está disponible después del primer bloque porque `expire_on_commit=False`. No crea `cliente` (el personal no es cliente).

### D-06 — Asignación (`POST /usuarios/{id}/roles`)
Contrato `AsignacionRolIn(rol: Literal["ADMIN","VENDEDOR","CLIENTE"], vence_en: AwareDatetime | None = None)` con `AfterValidator` que exige `vence_en > now(UTC)` → 422 (`AwareDatetime` ya rechaza la fecha sin zona con 422). Salida `AsignacionRolOut {id, usuario_id, rol, desde, vence_en, revocada_en, otorgada_por, vigente}` (`vigente` calculado al responder).
En un solo bloque:
1. `abierta = await uow.asignaciones.get_abierta(usuario_id, rol)` (la fila con `revocada_en IS NULL`; a lo sumo una por el índice).
2. Si `abierta` está vigente → 409 `"El usuario ya tiene ese rol vigente"`.
3. Si `abierta` venció → `abierta.revocada_en = ahora`; `update` (flush) — **cierra** la fila (no la borra) para que el índice parcial admita la nueva.
4. `add(AsignacionRol(usuario_id, rol, vence_en, otorgada_por=actor.id))` → flush: SQLSTATE 23503 (FK de `usuario_id`) → **404** `"Usuario no encontrado"` (sin consultar antes el usuario); 23505 (dos asignaciones cruzadas) → 409 con el mismo mensaje del paso 2.
5. `add(EventoSeguridad(actor=actor.email, accion=f"Asignación de rol {rol} al usuario {usuario_id}" + vencimiento si hay))`.
La lectura del paso 1 es la **excepción declarada** de la regla "no pre-consultar unicidad" (CLAUDE.md, RN-03/RN-05): hace falta para distinguir "vigente → 409" de "vencida → cerrar y reabrir"; el índice único parcial sigue siendo el garante. El evento nombra al usuario por id para no leerlo (la FK ya prueba que existe).

### D-07 — Revocación (`DELETE /usuarios/{id}/roles/{rol}`) y autoprotección
`{rol}` tipado como `Literal`/`Enum` de los tres roles → 422 si no es válido. En un solo bloque:
1. Si `rol == "ADMIN"` y `usuario_id == actor.id` → 409 `"Un administrador no puede revocarse su propio rol ADMIN"` (antes de leer nada).
2. `abierta = await uow.asignaciones.get_abierta(usuario_id, rol)`; si no hay → 404 `"El usuario no tiene ese rol asignado"` (cubre también el usuario inexistente; mismo mensaje).
3. Si `rol == "ADMIN"` y `abierta` está vigente: `await uow.asignaciones.contar_admins_vigentes(ahora)` (usuarios **activos** con ADMIN vigente, una consulta con `JOIN usuario`); si ≤ 1 → 409 `"El sistema no puede quedarse sin administradores"`.
4. `abierta.revocada_en = ahora`; `update`; `add(EventoSeguridad(actor=actor.email, accion=f"Revocación de rol {rol} al usuario {usuario_id}"))`. 200 con `AsignacionRolOut`.
Revocar una asignación abierta pero ya vencida también la cierra (200): deja el historial prolijo y no cambia permisos.
Nota: como el actor necesita ADMIN vigente para llegar acá (D-01) y no puede revocarse el propio (paso 1), el paso 3 solo se dispara si el actor deja de ser administrador vigente entre la autorización y la revocación (p. ej. su `vence_en` pasa en ese instante). Se implementa igual por la regla "nunca sin administradores" y se verifica con una llamada directa al servicio (tarea 6.5), porque por HTTP no es alcanzable de forma determinística.

### D-08 — Historial (`GET /usuarios/{id}/roles` y `GET /eventos`)
- `GET /usuarios/{id}/roles`: `uow.usuarios.get_by_id(id)` → 404 `"Usuario no encontrado"` (es una lectura, no una pre-consulta antes de escribir); luego `uow.asignaciones.listar_de_usuario(id)` ordenado por `desde, id`. Sin paginar: la tabla de la consigna no le da `page`/`size` y el historial de un usuario es corto.
- `GET /eventos`: `PaginacionDep`; `uow.eventos.contar()` y `uow.eventos.listar_recientes(offset, limit)` ordenado por `cuando DESC, id DESC`; `verificar_pagina` → 422 fuera de rango; `PaginatedResponse[EventoOut]`. Mismo patrón que los listados de C-09.
Métodos nuevos de repositorio (en `usuarios/repository.py`, sin `commit`, nombrados por lo que traen): `AsignacionRolRepository.get_abierta`, `listar_de_usuario`, `contar_admins_vigentes`; `EventoSeguridadRepository.listar_recientes`.

### D-09 — Dónde viven los routers nuevos
En `app/modules/usuarios/router.py`, junto al de `/auth`: `router` (`/auth`, abierto, sin cambios), `personal_router` (`/usuarios`) y `eventos_router` (`/eventos`), ambos con `dependencies=[Depends(requiere_rol(ADMIN))]` y montados en el grupo protegido. Servicio nuevo en `usuarios/service.py` (`alta_personal`, `listar_roles`, `asignar_rol`, `revocar_rol`, `listar_eventos`), recibiendo el UoW sin abrir y el `UsuarioActual` del actor. Contratos en `usuarios/schemas.py`. La consigna ubica `EventoSeguridad` y `AsignacionRol` en el módulo `usuarios`.

### D-10 — Traducción de `IntegrityError` por SQLSTATE
Se agrega `_es_fk(exc)` (23503) junto a `_es_unicidad` (23505) en `usuarios/service.py`. Todo `IntegrityError` no reconocido se relanza al manejador global (409 genérico, sin texto de la base). Ningún mensaje nombra tablas ni restricciones.

### D-11 — Pruebas (equivalente RED/GREEN sin runner)
- **Preparación** `test/C-12-preparacion.sql` (se corre con `psql` después de `python scripts/seed.py`): crea o restablece `admin@example.com`, `admin2@example.com` (ADMIN), `vendedor@example.com` (VENDEDOR) y `nuevo@example.com` (VENDEDOR, `debe_cambiar_password = true`) con contraseñas de mentira cuyos hashes bcrypt se calculan una vez en el apply y se pegan en el archivo; es idempotente (`INSERT … ON CONFLICT (email) DO UPDATE`, cierra con `revocada_en` las asignaciones abiertas de esos usuarios e inserta las nuevas; nunca `DELETE` sobre `asignacion_rol`). Lleva un comentario: provisorio hasta el `seed.py` de C-14, que lo reemplaza con los mismos correos.
- **Casos** `test/C-12-autorizacion.http`: varias sesiones a la vez (`# @name loginAdmin`, `loginAdmin2`, `loginVendedor`, `loginNuevo`, `loginCliente` de un registro con `{{$timestamp}}`), cada pedido con `# @no-cookie-jar` y `Cookie: {{loginX.response.headers.Set-Cookie}}`. Secciones: 401 vs 403 (C-06, parte de autorización), grupos y cambio obligatorio (C-09), alta de personal, asignación y vencimientos inválidos, revocación con la sesión abierta (C-07), autoprotección (C-08), `/eventos`. Cada pedido con la respuesta esperada comentada y los `psql` de verificación (filas revocadas siguen, eventos por operación, ninguno por rechazos).
- **RED**: el archivo se escribe antes del código de cada grupo; las rutas nuevas dan 404/405 y las protegidas 2xx sin cookie (distinto del comentario). **GREEN**: el código mínimo hasta que coincidan.
- **Regresión** de C-01..C-10: los `.http` que tocan rutas protegidas suman al principio un pedido `### login de administrador (C-12)` contra `admin@example.com`; el resto de sus pedidos queda igual y se apoya en el cookie jar de REST Client (`rest-client.rememberCookiesForSubsequentRequests`, activo por defecto). Sus respuestas esperadas no cambian. Archivos a tocar (relevados con `grep` en el propose: llaman `POST`/`PATCH` del catálogo o rutas de clientes/ventas): `C-01` (`GET /clientes/abc`: con la sesión da 422, que es justo lo que pide el caso C-01 de la consigna), `C-02`, `C-03`, `C-04`, `C-05`, `C-06`, `C-07`, `C-09-paginacion`, `C-10` y `extras-endpoints.http`. `C-08-arranque-y-health.http` y `C-08-busqueda-segura.http` solo usan rutas abiertas y no cambian; `C-11-autenticacion.http` no se toca. `PATCH /ventas/2` de C-06 sigue dando 405: el enrutador responde 405 por método antes de resolver dependencias.

### D-12 — Sin MODIFIED sobre las capacidades existentes
Los escenarios de `endpoints-crud`, `altas-*`, `lecturas-ventas`, `transacciones-venta`, etc. envían peticiones a rutas que ahora son protegidas sin mencionar la sesión. En lugar de reescribir cada requisito (decenas de escenarios que no cambian de comportamiento para quien tiene permiso), `matriz-permisos` declara el requisito "Escenarios de otras capacidades presuponen el permiso". Así el archivo de esos specs no cambia y el contrato queda explícito en un solo lugar.
*Alternativa*: MODIFIED de `endpoints-crud` (5 requisitos) → mucho texto duplicado y aun así quedarían sin tocar los de `altas-*` y `ventas`.

### Supuestos y ambigüedades (todos confirmados o decididos por el usuario)
- **S-01 (confirmado por el usuario)** `GET /editoriales/{id}/libros`, `/generos/{id}/libros` y `/autores/{id}/libros` son **abiertas (Cualquiera)**, no ADMIN como dicen la KB (`03_actores_y_roles.md`, marcado `(*)`) y DD-12. La re-alineación de la tabla da 2 filas "Abierto GET … Cualquiera" en la pág. 17 y exactamente 12 filas ADMIN para las 12 rutas de administración y catálogo; además el catálogo es público. Si el usuario confirma lo contrario, solo cambia la fila de la tabla D-04 y un requisito de `matriz-permisos`.
- **S-02 (decidido por el usuario: solo ADMIN)** `GET /ventas` (listado) es **solo ADMIN**, como dice `CHANGES.md` [C-13]; la lectura "VENDEDOR o ADMIN" de la consigna re-alineada y la KB se descartó. Ojo con la diferencia: `GET /ventas/{id}` es en C-12 VENDEDOR o ADMIN (provisorio, S-04) hasta que C-13 lo reemplace por la decisión de dueño. La KB (`03_actores_y_roles.md`) debe alinearse con esta decisión.
- **S-03 (confirmado por el usuario)** Rutas del TP que la tabla no lista (IN-04), conservadas: `GET /editoriales/{id}`, `GET /generos/{id}`, `GET /autores/`, `GET /autores/{id}` → **abiertas** (familia del catálogo público); `PATCH /generos/{id}` → **ADMIN** (como los otros PATCH del catálogo); `GET /clientes/` → **VENDEDOR o ADMIN** (familia de clientes). Ninguna se borra. Alternativa a decidir por el usuario/docente: quitarlas.
- **S-04 (confirmado por el usuario)** `GET /ventas/{id}` en C-12: grupo protegido **con `requiere_rol(VENDEDOR, ADMIN)` provisorio**, para no abrir ventas ajenas a los clientes entre C-12 y C-13. C-13 lo **reemplaza** por la decisión de dueño en el servicio (sin `requiere_rol`, como pide la consigna) y modifica el requisito "Detalle de venta protegido sin decisión de dueño todavía". Alternativa: dejarla solo autenticada ya en C-12 (cumple la consigna en la forma pero deja ver ventas ajenas hasta C-13).
- **S-05** Mensajes: 403 sin rol `"No tenés permiso para esta operación"`; 403 cambio pendiente `"Tenés que cambiar la contraseña antes de seguir"`; 409 `"El usuario ya tiene ese rol vigente"`, `"Un administrador no puede revocarse su propio rol ADMIN"`, `"El sistema no puede quedarse sin administradores"`; 404 `"Usuario no encontrado"`, `"El usuario no tiene ese rol asignado"`.
- **S-06** Alta de personal: el administrador envía la contraseña provisoria en el cuerpo (`password`, mínimo 8, máximo 72 bytes) y el rol (`ADMIN` o `VENDEDOR`); el alta no crea ficha de `cliente`; sin vencimiento.
- **S-07** `POST /usuarios/{id}/roles` acepta los tres roles (incluido `CLIENTE`) porque el CHECK de la base los admite; `vence_en` solo en la asignación, no en el alta.
- **S-08** "Cerrar la fila anterior" al reasignar un rol vencido = escribir su `revocada_en` (el índice parcial solo mira `revocada_en IS NULL`).
- **S-09** `GET /usuarios/{id}/roles` devuelve todo el historial (no solo los vigentes), sin paginar.
- **S-10** Texto de `accion` en `evento_seguridad`: `"Alta de personal <correo> con rol <rol>"`, `"Asignación de rol <rol> al usuario <id>[ hasta <vence_en>]"`, `"Revocación de rol <rol> al usuario <id>"`; `actor` = correo del administrador. El evento `SISTEMA` del seed es C-14.
- **S-11** La autoprotección cuenta solo usuarios **activos** con `ADMIN` vigente.
- **S-12** `POST /auth/logout` sigue sin exigir sesión (S-03 de C-11) y queda en el grupo abierto.

## Risks / Trade-offs

- [`.http` de C-01..C-10 rotos al proteger las rutas] → la tarea 7 les suma un login y se corre la regresión completa; el `.sql` de preparación es requisito previo y se dice al principio de cada archivo.
- [Cookie jar compartido entre archivos de REST Client: un `logout` de C-11 o de C-12 deja sin sesión al archivo siguiente] → cada archivo de regresión hace su propio login al principio; `C-12` usa `@no-cookie-jar` en todos sus pedidos para no pisar el jar.
- [Hashes bcrypt de contraseñas de mentira en `test/C-12-preparacion.sql`] → son de prueba, como las del seed de la consigna; el archivo lo dice y C-14 lo reemplaza. Nunca contraseñas reales.
- [Ruta registrada en los dos grupos o en ninguno] → tarea de inventario: listar `app.routes` y compararla con `matriz-permisos` (camino, método, grupo, rol).
- [Olvidar `requiere_rol` en una ruta protegida nueva (C-13)] → la ruta queda igual con 401 y bloqueo por cambio pendiente (protección por defecto), pero abierta a cualquier autenticado; `matriz-permisos` exige declararla al agregarla.
- [Carrera: dos administradores se revocan `ADMIN` mutuamente a la vez y quedan cero] → fuera de alcance (cap. 7); el conteo del paso 3 de D-07 no toma bloqueos.
- [`core/dependencies.py` importa el repositorio de `usuarios`] → dependencia de core a un módulo, ya aceptada en C-11 para el modelo; no hay ciclo (el repositorio no importa `dependencies`).
- [S-04 provisorio olvidado en C-13] → el caso C-06 de la consigna ("la cliente ve su venta, 200") falla si no se quita, y el requisito queda marcado como provisorio en `matriz-permisos`.

## Migration Plan

- **Sin migración**: no hay cambios de esquema (0001–0004 intactas; `asignacion_rol`, `evento_seguridad` y `usuario.debe_cambiar_password` vienen de la 0003). Se verifica con `alembic check` / `alembic revision --autogenerate` en seco sin diferencias (tarea 8.3).
- Despliegue: reiniciar la aplicación. Antes de usar las rutas protegidas tiene que existir al menos un administrador (en desarrollo, `test/C-12-preparacion.sql`; en la entrega, el `seed.py` de C-14).
- Rollback: revertir el commit; las filas creadas por las pruebas se restablecen con el `.sql` de preparación o el seed.

## Open Questions

- Texto exacto de los mensajes y de `accion` (S-05, S-10): se pueden ajustar sin cambiar specs más allá de los literales.
