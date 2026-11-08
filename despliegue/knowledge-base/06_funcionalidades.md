# Funcionalidades

Organizadas por **épica = ejercicio de la consigna** (7 épicas = 7 changes del roadmap) y luego por historia (US-NNN).

## Épica 1: Proyecto, conexión y ciclo de vida (10 pts)

### US-001 — Estructura y arranque
**Como** desarrollador **quiero** el proyecto con la estructura por módulos y el motor creado en el `lifespan` **para** tener una base de trabajo común.

**Criterios de aceptación**:
- [ ] Existen `app/main.py`, `app/core/config.py`, `app/core/database.py` y los 7 módulos con `models/schemas/service/router`.
- [ ] El motor y la fábrica de sesiones se crean en el `lifespan`, se guardan en `app.state` y el motor se cierra al apagar.
- [ ] `get_session` entrega una sesión por petición con `expire_on_commit=False`.
- [ ] `DATABASE_URL` se lee de `.env`; existe `env.example` sin secretos.

### US-002 — Health
**Como** operador **quiero** `GET /health/live` y `GET /health/ready` **para** saber si la API y la base responden.

- [ ] `live` devuelve `{"estado": "vivo"}` sin tocar la base.
- [ ] `ready` ejecuta `SELECT 1` y devuelve el estado de la base.

## Épica 2: Modelos, restricciones y relaciones (25 pts)

### US-003 — Modelos de tabla
**Como** desarrollador **quiero** los 9 modelos con todas sus restricciones **para** que la base garantice la integridad.

- [ ] UNIQUE, CHECK, claves foráneas e índices según `04_modelo_de_datos.md`.
- [ ] Navegación en los dos extremos de cada FK; `Cliente.perfil` devuelve un objeto.
- [ ] `LibroAutor` es entidad propia (objeto de asociación), no `link_model`.
- [ ] Dinero con `Decimal`.

**Reglas relacionadas**: RN-01, RN-02, RN-03, RN-09.

## Épica 3: Migraciones (10 pts)

### US-004 — Dos migraciones autogeneradas
**Como** desarrollador **quiero** versionar el esquema con Alembic **para** crearlo sin `create_all`.

- [ ] Plantilla asincrónica; sin credenciales en `alembic.ini`.
- [ ] Migración 1: todas las tablas menos `genero`. Migración 2: agrega `genero` y `libro.genero_id`. Ambas con `--autogenerate`.
- [ ] Cada migración se lee y, si hace falta, se corrige a mano con un comentario explicativo.
- [ ] `alembic upgrade head` sobre una base vacía y `downgrade -1` + `upgrade head` funcionan.

## Épica 4: Contratos y CRUD (15 pts)

### US-005 — CRUD de referencia
**Como** operador **quiero** crear, listar, ver y modificar editoriales, géneros, autores, libros y clientes **para** mantener los datos maestros.

- [ ] DTO `Create`, `Update`, `Read` separados de los modelos de tabla; los de alta no llevan `id`.
- [ ] `PATCH` aplica solo los campos enviados (`exclude_unset`).
- [ ] 201 al crear, 404 si no existe, 409 si la base rechaza, 422 si el contrato no se cumple.
- [ ] Listados paginados (RN-10); búsqueda por título con parámetros ligados (RN-11).

**Reglas relacionadas**: RN-01, RN-02, RN-03, RN-10, RN-11, RN-12.

## Épica 5: Altas con relaciones: ids y datos (20 pts)

### US-006 — Alta de libro con autores
**Como** operador **quiero** crear un libro enviando `editorial_id`, `genero_id` y `autores` (`autor_id`, `rol`, `orden`) **para** registrar las agregaciones y la autoría.

- [ ] Ningún `if` consulta antes si un id existe: se escribe y un FK rechazado responde 409 con mensaje propio.

### US-007 — Perfil del cliente
**Como** operador **quiero** `POST /clientes/{id}/perfil` **para** cargar teléfono y dirección.

- [ ] Un segundo perfil para el mismo cliente responde 409 (RN-09).

### US-008 — Alta de venta con renglones
**Como** operador **quiero** crear una venta con `cliente_id` y `renglones` (`libro_id`, `cantidad`) **para** registrar un hecho de venta.

- [ ] El precio de cada renglón se copia del libro; el total lo calcula el servidor; la fecha la pone el servidor.
- [ ] Mínimo un renglón y sin libro repetido (422). Cliente o libro inexistente responde 409 con mensaje propio.
- [ ] Respuesta 201 con cliente y renglones (`titulo`, `precio_unitario`, `subtotal`).

**Reglas relacionadas**: RN-04, RN-05, RN-06, RN-07, RN-08, RN-12.

## Épica 6: Lecturas sin N+1 (10 pts)

### US-009 — Detalles con carga anticipada
**Como** operador **quiero** ver el detalle de un libro (editorial, género, autores) y de una venta (cliente, renglones) **para** consultar la información completa.

- [ ] `joinedload` para relaciones a uno y `selectinload` para colecciones, declarados en la misma consulta.
- [ ] El número de consultas es fijo e independiente de la cantidad de autores o renglones.
- [ ] Ninguna lectura depende de carga perezosa. Evidencia C-07 en la consola.

## Épica 7: Asincronía sin bloqueos (10 pts)

### US-010 — Aviso de comprobante en segundo plano
**Como** cliente **quiero** recibir el aviso del comprobante **para** confirmar mi compra.

- [ ] Al registrar una venta se agenda con `BackgroundTasks` un aviso simulado con `await asyncio.sleep(0.5)` y un log.
- [ ] Corre después de enviar la respuesta; el servidor sigue atendiendo otras peticiones.
- [ ] Ningún handler ejecuta llamadas bloqueantes.

## Entregables transversales

- Script async de datos iniciales; archivos `.http` en `test/` con los casos C-01 a C-08 (cada uno con su respuesta esperada en un comentario); `README.md` desde cero; `requirements.txt`.
