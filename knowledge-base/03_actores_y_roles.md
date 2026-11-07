# Actores y Roles

> **TP caps 1-4 (implementado)**: no había actores autenticados ni roles; todo era abierto (Operador, Corrector, Grupo). **Parcial (pendiente)**: lo reemplaza por el modelo de esta página.

## Actores del sistema

| Actor | Rol en la base | Descripción | Cómo interactúa |
|---|---|---|---|
| Administrador | `ADMIN` | Mantiene catálogo, repone stock, administra personal y roles | API autenticada (cookie) |
| Vendedor | `VENDEDOR` | Registra ventas y atiende clientes en el mostrador | API autenticada |
| Cliente | `CLIENTE` | Se registra solo en la web y consulta sus compras | `/auth/registro`, `/mis-ventas`, su `/ventas/{id}` |
| Visitante | — | Navega el catálogo sin sesión | Rutas del grupo abierto |
| Corrector (docente) | — | Ejecuta `.http`, mira consola, prueba la URL del VPS | REST Client, psql, docker |
| Grupo de desarrollo | — | Construye y entrega | Repo, migraciones, README |
| `SISTEMA` | texto, no usuario | Actor del evento "Carga de los datos iniciales" | `seed.py` |

## Modelo de roles

- `usuario` **no tiene columna `rol`**: los roles son las filas **vigentes** de `asignacion_rol` (no revocadas y sin vencer).
- Rol ∈ {`ADMIN`, `VENDEDOR`, `CLIENTE`} (CHECK en la base).
- Revocar escribe `revocada_en`; la fila no se borra (historial). Reasignar un rol vencido cierra la fila anterior y abre una nueva.
- El permiso se decide con los roles **leídos de la base en cada petición** (RN-04). Los roles dentro del JWT son solo informativos (`GET /auth/yo` muestra ambos conjuntos).
- Un cliente puede tener o no `usuario_id` (acceso web opcional).

## Códigos de seguridad

- **401**: no hay cookie, token inválido o vencido, o el usuario no existe / está inactivo (`get_usuario_actual`).
- **403**: autenticado pero sin el rol vigente (`requiere_rol`), con cambio de contraseña pendiente, o sin relación con la venta pedida.
- Toda ruta del grupo protegido responde además 401 sin sesión y 403 con el cambio de contraseña pendiente.
- El token viaja **solo** en la cookie `access_token` (HttpOnly, SameSite=Lax, Max-Age = duración del token, Secure configurable); nunca se lee de `Authorization`.

## Grupos de rutas (se montan en `main.py`)

| Grupo | Control | Contenido |
|---|---|---|
| **Abierto** | No pide sesión | `/health/*`, `/auth/*` (debe poder usarse para iniciar sesión), catálogo público: `GET /libros`, `GET /libros/{id}`, `GET /editoriales`, `GET /generos` |
| **Protegido** | Lleva el control del cambio obligatorio de contraseña **montado una sola vez** (FastAPI suma dependencias y no las resta) | Todo lo demás |

Un usuario con `debe_cambiar_password = true` solo puede usar `/auth` y las rutas que no piden sesión (RN-06).

## Matriz de endpoints y roles (Parcial)

> Reconstruida de una tabla del PDF con columnas entrelazadas. Códigos marcados con (*) son inferidos por orden de aparición; ver `10_preguntas_abiertas.md` (IN-03). Los roles de "Quién" se contrastaron fila a fila.

| Grupo | Método | Ruta | Quién | Códigos |
|---|---|---|---|---|
| Abierto | GET | `/health/live` | Cualquiera | 200 |
| Abierto | GET | `/health/ready` | Cualquiera | 200, 503 |
| Abierto | POST | `/auth/registro` | Cualquiera | 201, 409, 422 |
| Abierto | POST | `/auth/login` | Cualquiera | 200, 401, 422, 429 |
| Abierto | POST | `/auth/logout` | Cualquiera | 200 |
| Abierto | GET | `/auth/yo` | Autenticado | 200, 401 |
| Abierto | POST | `/auth/cambiar-password` | Autenticado | 200, 401, 422 |
| Abierto | GET | `/libros` (`page`, `size`, `titulo`, `genero_id`) | Cualquiera | 200, 422 |
| Abierto | GET | `/libros/{id}` | Cualquiera | 200, 404, 422 |
| Abierto | GET | `/editoriales`, `/generos` (`page`, `size`) | Cualquiera | 200, 422 |
| Protegido | GET | `/editoriales/{id}/libros`, `/generos/{id}/libros`, `/autores/{id}/libros` | ADMIN (*) | 200, 404 |
| Protegido | POST | `/usuarios` (alta de personal, contraseña provisoria) | ADMIN | 201, 409, 422 (*) |
| Protegido | POST | `/usuarios/{id}/roles` | ADMIN | 201, 404, 409, 422 (*) |
| Protegido | GET | `/usuarios/{id}/roles` | ADMIN | 200, 404 (*) |
| Protegido | DELETE | `/usuarios/{id}/roles/{rol}` | ADMIN | 200, 404, 409 (*) |
| Protegido | GET | `/eventos` (`page`, `size`) | ADMIN | 200, 422 (*) |
| Protegido | POST | `/editoriales`, `/generos`, `/autores` | ADMIN | 201, 409, 422 |
| Protegido | PATCH | `/editoriales/{id}`, `/autores/{id}` | ADMIN | 200, 404, 409, 422 |
| Protegido | POST | `/libros` (con `autores` y `stock_inicial`) | ADMIN | 201, 409, 422 |
| Protegido | PATCH | `/libros/{id}` (título y precio; el stock no) | ADMIN | 200, 404, 409, 422 |
| Protegido | DELETE | `/libros/{id}` (baja lógica) | ADMIN | 204, 404 |
| Protegido | POST | `/libros/{id}/reponer` | ADMIN | 200, 404, 409, 422 (*) |
| Protegido | GET | `/libros/{id}/movimientos` | ADMIN | 200, 404 (*) |
| Protegido | POST | `/clientes` | VENDEDOR, ADMIN | 201, 409, 422 |
| Protegido | GET, PATCH | `/clientes/{id}` (con su perfil) | VENDEDOR, ADMIN | GET 200, 404; PATCH 200, 404, 409, 422 |
| Protegido | POST | `/clientes/{id}/perfil` | VENDEDOR, ADMIN | 201, 404, 409 |
| Protegido | GET | `/clientes/{id}/ventas` | VENDEDOR, ADMIN | 200, 404 |
| Protegido | POST | `/ventas` (con `renglones`) | VENDEDOR, ADMIN | 201, 409, 422 |
| Protegido | GET | `/ventas` (`page`, `size`) | VENDEDOR, ADMIN | 200, 422 |
| Protegido | GET | `/ventas/{id}` | El personal, o el cliente dueño | 200, 403, 404 |
| Protegido | GET | `/mis-ventas` (`page`, `size`) | Autenticado | 200, 422 |

### El detalle de una venta no lleva `requiere_rol`
`GET /ventas/{id}` no lleva `requiere_rol`: el cliente dueño no tiene rol de personal y recibiría un 403 injusto. La decide el **servicio**: primero quién es y qué relación tiene con la venta (403 si no es personal ni dueño) y recién después qué se devuelve (404 si no existe).

### Rutas del TP que la tabla no lista
`GET /editoriales/{id}`, `GET /generos/{id}/...`, `GET /autores/{id}`, `GET /clientes/...` extra y similares del TP no figuran en la tabla del Parcial. Ver `10_preguntas_abiertas.md` (IN-04).
