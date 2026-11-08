# Proposal

> **Governance: CRÍTICO** (autorización, roles, administración de personal, historial de seguridad). Este change produce solo artefactos de planificación. El `/opsx:apply` requiere **aprobación humana explícita** antes de escribir cualquier línea de código, y tiene puntos de control con aprobación (PC) en el código sensible: `requiere_rol` y el control del cambio obligatorio, la autoprotección y la revocación, el alta de personal y el cableado de la protección sobre los routers existentes. Ver `tasks.md`.

## Why

Después de C-11 el sistema sabe **quién** hace cada petición (`get_usuario_actual`, 401), pero no decide **qué** puede hacer: todas las rutas del dominio siguen abiertas, cualquiera crea libros o ventas sin sesión, nadie puede dar de alta personal ni asignar o revocar roles, y un usuario con `debe_cambiar_password` usa todo el sistema. El Ejercicio 5 del Parcial (12 pts) pide autorizar con los roles **vigentes leídos de la base en cada petición**, distinguir siempre 401 de 403, la autoprotección del administrador, los dos grupos de rutas con el control del cambio obligatorio montado una sola vez, y el historial de seguridad (RN-03..RN-06, RN-14, RN-16). C-13 (ventas y stock) necesita esta autorización para decidir el detalle de venta y registrar el usuario de cada movimiento.

## What Changes

- **`requiere_rol(*roles)`** en `app/core/dependencies.py`: depende de `get_usuario_actual` (401) y consulta en la **misma sesión** de la petición los roles vigentes del usuario (no revocados, sin vencer); si ninguno está permitido → **403**. Los roles del token no deciden nada. Revocar un rol quita el permiso a una sesión ya abierta en su petición siguiente. `get_usuario_actual` no cambia.
- **Control del cambio obligatorio de contraseña** (RN-06) en `app/core/dependencies.py`: 401 sin sesión, **403** si `debe_cambiar_password` es verdadero. Se monta **una sola vez**, como dependencia del grupo protegido.
- **Dos grupos de rutas en `app/main.py`**: el **abierto** (health, `/auth/*`, catálogo público) y el **protegido** (todo lo demás, con el control anterior). Cada `router.py` de dominio expone sus rutas abiertas y protegidas por separado y `main.py` las incluye en el grupo que corresponde.
- **Protección de las rutas existentes según la matriz de la consigna**: escrituras del catálogo (`POST`/`PATCH` de editoriales, géneros, autores y libros) → ADMIN; clientes (alta, lectura, edición, perfil, ventas del cliente) y `POST /ventas` → VENDEDOR o ADMIN, y el listado `GET /ventas` → solo ADMIN; lecturas del catálogo (`GET /libros`, `GET /libros/{id}`, `GET /editoriales`, `GET /generos` y los `…/{id}/libros`) → abiertas. **BREAKING** para quien usaba esas rutas sin sesión (incluidos los `.http` de C-01..C-10).
- **`GET /ventas/{id}`**: pasa al grupo protegido. La decisión "personal o cliente dueño" se toma en el servicio en C-13; hasta entonces queda **provisoriamente** restringida al personal (supuesto S-04 de `design.md`, confirmado por el usuario). Nótese la diferencia: el listado `GET /ventas` es solo ADMIN (S-02), el detalle `GET /ventas/{id}` es VENDEDOR o ADMIN hasta C-13.
- **Alta de personal** `POST /usuarios` (ADMIN): crea un usuario con contraseña provisoria, rol VENDEDOR o ADMIN y `debe_cambiar_password = true`, más la línea de `evento_seguridad`, en **un solo** bloque de Unit of Work; el hash se calcula fuera de la transacción; correo repetido → 409 sin pre-consulta.
- **Roles con vigencia** (ADMIN): `GET /usuarios/{id}/roles` (historial), `POST /usuarios/{id}/roles` (vencimiento opcional, con zona y en el futuro; si no → **422**; rol vigente repetido → **409**; reasignar un rol vencido cierra la fila anterior y abre otra) y `DELETE /usuarios/{id}/roles/{rol}` (escribe `revocada_en`, nunca borra). **Autoprotección** (RN-05): un administrador no se revoca su propio ADMIN y el sistema nunca queda sin administradores vigentes → **409**.
- **Historial de seguridad** (RN-16): cada alta de personal, asignación y revocación deja una línea en `evento_seguridad` en la **misma** transacción; `GET /eventos` (ADMIN) lo lista con el envoltorio `{items, total, page, size, pages}`.
- **Pruebas**: `test/C-12-autorizacion.http` con varias sesiones a la vez (`# @name`, `# @no-cookie-jar`, cookie a mano) para los casos C-06 (parte 401/403), C-07, C-08 y C-09 de la consigna; `test/C-12-preparacion.sql` con los usuarios de personal de la consigna (provisorio hasta el seed de C-14); los `.http` de C-01..C-10 suman un login al principio para seguir dando lo mismo.

## Capabilities

### New Capabilities

- `autorizacion-roles`: decisión de permisos con los roles vigentes leídos de la base en cada petición, 403 frente a 401, misma sesión que el Unit of Work y roles del token solo informativos.
- `grupos-de-rutas`: grupo abierto y grupo protegido, el control del cambio obligatorio de contraseña montado una vez y qué puede usar un usuario con el cambio pendiente.
- `matriz-permisos`: qué rol exige cada ruta de la API (abierta, autenticada, VENDEDOR/ADMIN o ADMIN), incluidas las rutas del TP que la tabla de la consigna no lista.
- `alta-personal`: alta de un usuario de personal con contraseña provisoria y cambio obligatorio, atómica con su rol y su evento.
- `administracion-roles`: consulta, asignación con vencimiento y revocación de roles, reasignación de un rol vencido y autoprotección del administrador.
- `historial-seguridad`: qué operaciones dejan una línea en `evento_seguridad`, en la misma transacción, y el listado paginado `GET /eventos`.

### Modified Capabilities

(ninguna) — Los requisitos existentes siguen valiendo para quien tiene el permiso: `matriz-permisos` declara que los escenarios de otras capacidades sobre rutas protegidas presuponen una sesión con un rol permitido, en lugar de reescribir cada uno (ver design D-12).

## Impact

- **Código nuevo**: `requiere_rol` y el control del cambio obligatorio en `app/core/dependencies.py`; en `app/modules/usuarios/`: contratos de personal, roles y eventos (`schemas.py`), métodos de repositorio (asignación abierta, historial, administradores vigentes, eventos paginados), servicio de personal/roles/eventos y los routers `/usuarios` y `/eventos`; `test/C-12-autorizacion.http`, `test/C-12-preparacion.sql`.
- **Código modificado**: `app/main.py` (C-08/C-09/C-11: dos grupos de rutas), los `router.py` de `editoriales`, `generos`, `autores`, `libros`, `clientes` y `ventas` (separar rutas abiertas y protegidas, agregar `requiere_rol`), `app/modules/usuarios/router.py` (C-11: se monta en el grupo abierto, sin cambios en sus rutas). Los servicios de dominio **no cambian**.
- **Pruebas modificadas**: los `.http` de C-01..C-10 que tocan rutas protegidas suman un login de administrador al principio (sin cambiar sus respuestas esperadas).
- **Esquema**: **sin migración** — `asignacion_rol` (con su índice único parcial), `evento_seguridad` y `usuario.debe_cambiar_password` ya existen desde la 0003 (C-10).
- **API**: 5 rutas nuevas (`POST /usuarios`, `GET`/`POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}`, `GET /eventos`); las rutas protegidas responden además 401 sin sesión y 403 sin el rol o con el cambio de contraseña pendiente.
- **Fuera de alcance**: `/mis-ventas`, la decisión de dueño de `GET /ventas/{id}`, `DELETE /libros/{id}`, `reponer` y `movimientos` (C-13); usuarios del seed (C-14); carreras entre dos administradores que se revocan a la vez (cap. 7).
