# Design

## Context

El estado observable del repo ya incluye el CRUD paginado de C-04, el handler global de `IntegrityError`→409 y `DataError`→422 en `app/core/errors.py`, `PaginatedResponse` en `app/core/paginacion.py`, `BaseRepository`/`SoftDeleteRepository` y `UnitOfWork`, además de `POST /clientes/{id}/perfil` y `POST /ventas/` parcialmente implementados. `POST /libros/` solo crea el `Libro`; `POST /ventas/` hace `flush` sin `commit`, devuelve 400/409 donde la consigna pide 422 y no expone `titulo`. Motivación y alcance: `proposal.md`. Requisitos: `specs/altas-libros-autores/`, `specs/altas-perfil-cliente/`, `specs/altas-ventas/`, `specs/transacciones-venta/`.

Restricciones que condicionan el diseño:
- Reglas duras (`AGENTS.md`): sin `create_all`; dinero con `Decimal`/`NUMERIC`; nunca pre-consultar unicidad ni existencia de ids; nunca devolver texto interno de la base; sin carga perezosa (`lazy="raise"`); todos los handlers `async def`; `ConfigDict(extra="forbid")` en todo DTO de entrada; sin credenciales en el repo.
- La base y sus tablas (`libro_autor`, `perfil_cliente`, `venta`, `renglon_venta`) ya existen vía Alembic; C-05 no agrega migraciones.
- El stock no se descuenta al vender (SU-01) y no existe `PATCH` de ventas (RN-08).
- La respuesta de venta se calcula íntegramente en el servidor (RN-06, RN-07) y la fecha la pone el servidor.

## Goals / Non-Goals

**Goals:**
- Alta de libro + autorías atómica, sin pre-consultas de ids, con validación de contrato 422 y errores de base 409.
- Alta de perfil con 201 y 409 tanto por RN-09 como por cliente inexistente (mensajes propios distintos), sin pre-consultar.
- Alta de venta validada en el DTO (422), persistida de verdad (commit), con precio copiado, total/subtotales con `Decimal` y `titulo` en la respuesta.
- Infraestructura de tests automatizados (`pytest`, `pytest-asyncio`, `httpx` + `ASGITransport`) con base de prueba real creada por Alembic.

**Non-Goals:**
- Optimización o conteo de consultas N+1 (C-06); solo se precarga lo necesario para no violar `lazy="raise"`.
- `BackgroundTasks` del comprobante (C-07).
- Cambios de esquema, migraciones nuevas, autenticación/RBAC, descuento de stock.
- Reconciliar la KB con las tablas extra (`usuario`, `movimiento_stock`, soft delete) ya presentes en el código.

## Decisions

### D-01 — Cuatro capabilities nuevas, sin tocar los specs de datos

`altas-libros-autores`, `altas-perfil-cliente`, `altas-ventas` y `transacciones-venta` describen comportamiento nuevo de la API. No se modifican `catalog-data`, `customer-data` ni `sales-data` porque el esquema no cambia. Los deltas de C-04 (`contratos-*`, `endpoints-crud`, `handler-integridad-global`) todavía no están archivados en `openspec/specs/`, así que no se usan como paths de modificaciones.

**Alternativas descartadas**: reutilizar `endpoints-crud` (su path no existe como spec archivado) y mezclar todo en una sola capability (perdería la separación entre contrato, escritura y atomicidad).

### D-02 — Contrato de `LibroCreate` con `autores` opcional y validaciones 422

Se agrega `autores: list[LibroAutorCreate] = []`, con `LibroAutorCreate` compuesto por `autor_id: int`, `rol: Literal["autor", "coautor", "traductor", "ilustrador"]` y `orden: int = Field(ge=1)`. `genero_id` pasa a ser **obligatorio en el DTO** (`genero_id: int`, sin default) por decisión del usuario, aunque la columna `libro.genero_id` admita NULL: la API exige género en el alta del Ejercicio 5 y la base sigue aceptando NULL para filas existentes. Se agregan `precio: Decimal = Field(gt=0)` y `stock_inicial: int = Field(ge=0)` para que RN-03 responda 422 desde el DTO y no dependa del CHECK de la base. Un `model_validator(mode="after")` rechaza `autor_id` repetido dentro de `autores` con 422.

`autores` queda opcional para no romper el alta de libro sin autorías que ya documentan los `.http` de C-04; el Ejercicio 5 se cumple cuando se envía la lista. La respuesta sigue siendo `LibroRead` (sin autorías anidadas): el detalle de autores es C-06.

**Alternativas descartadas**: hacer `autores` obligatorio (rompe el contrato previo y el `.http` sin autores) y dejar `genero_id` opcional (el usuario pidió exigirlo en el contrato del Ejercicio 5).

### D-03 — Alta de libro atómica con `UnitOfWork`

`crear_libro` abre `async with UnitOfWork(session):`; agrega el `Libro` con el repositorio (el `flush` asigna `id`) y luego agrega las filas `LibroAutor(libro_id=libro.id, autor_id=..., rol=..., orden=...)`. No hay ningún `if` que consulte editorial, género o autor: si la base rechaza ISBN/FK/CHECK, el `IntegrityError` sale del bloque, `UnitOfWork.__aexit__` hace `rollback` y el handler global responde 409. El commit de `UnitOfWork` persiste todo junto.

**Alternativas descartadas**: `session.add` + un único `session.commit()` sin `UnitOfWork` (menos explícito y repetido en cada service) y crear las autorías a través de `libro.autorias` (funciona en objetos nuevos, pero la carga perezosa está prohibida y el flujo explícito es más predecible).

### D-04 — Validación de `VentaCreate` en el DTO, no en el service

`VentaCreate` incorpora un `model_validator(mode="after")` que:
- rechaza `renglones` vacío con `ValueError` (422);
- rechaza `libro_id` repetido con `ValueError` (422).

`RenglonVentaCreate.cantidad` ya tiene `gt=0` (422). Se eliminan del service el 400 por lista vacía y el 409 por libro repetido, porque la consigna y RN-05 piden 422 y el Flujo 1 exige que el router/DTO valide antes de ejecutar el service.

**Alternativas descartadas**: mantener las validaciones en el service con `HTTPException` (códigos actuales incorrectos) y validar con una consulta a la base (prohibido).

### D-05 — Alta de venta persistente con `UnitOfWork` y prelectura de precios

`crear_venta` envuelve las escrituras en `async with UnitOfWork(session):`. Primero lee todos los libros pedidos en **una** consulta `select(Libro).where(Libro.id.in_(ids))` para cumplir RN-06 (SU-03 permite esa lectura). Si falta un libro, lanza 409 con mensaje propio antes de escribir. La existencia del cliente no se consulta: se deja que la FK de `venta.cliente_id` la rechace y el handler global traduzca a 409. Luego agrega la `Venta` (flush para obtener `id`) y los `RenglonVenta` con el `precio_unitario` copiado; al salir del bloque, `UnitOfWork` confirma. Ante cualquier excepción, revierte.

**Alternativas descartadas**: `expire_on_commit=False` + commit manual (funciona, pero el proyecto ya tiene `UnitOfWork` y centraliza commit/rollback) y consultar el cliente antes de insertar (prohibido).

### D-06 — `RenglonVentaRead.titulo` y respuesta de venta sin objeto cliente anidado

`RenglonVentaRead` agrega `titulo: str`. En el alta se construye con el mapa `id → Libro` ya leído para los precios. En `GET /ventas/` y `GET /ventas/{id}` se precarga el libro en la misma consulta (`.joinedload(RenglonVenta.libro)` o `selectinload(Venta.renglones).joinedload("libro")`) para poder leer `titulo` sin disparar `lazy="raise"`. `VentaRead` conserva `cliente_id` y no anida el objeto cliente: el contrato de C-04 ya identifica al cliente por id y el paréntesis de la consigna enumera solo los campos nuevos del renglón. Anidar el cliente obligaría a precargarlo también en el listado y ampliaría el contrato sin pedido explícito.

**Alternativas descartadas**: agregar `cliente: ClienteRead` a `VentaRead` (cambio de contrato mayor y precarga extra en listados) y dejar que el DTO acceda a `renglon.libro.titulo` sin precarga (viola `lazy="raise"`).

### D-07 — Perfil: ruta autoritativa y distinción UNIQUE/FK por SQLSTATE

`PerfilClienteCreate` mantiene `telefono` y `direccion`; `cliente_id` pasa a ser opcional en el cuerpo. El service usa siempre el `id` de la ruta; si el cuerpo trae un `cliente_id` distinto, responde 422 antes de escribir. La inserción se hace dentro de `UnitOfWork`. Al capturar `IntegrityError`, se inspecciona el SQLSTATE del error original de asyncpg (sin exponerlo): `23505` (UNIQUE) → 409 "El cliente ya tiene un perfil asociado"; `23503` (FK) → 409 "Cliente no encontrado"; cualquier otro caso se relanza al handler global. Ambos casos comparten el código 409 (consistencia con el resto de las altas con FK) pero con mensajes propios distintos. La extracción contempla `exc.orig.sqlstate` y, como respaldo, `exc.orig.__cause__.sqlstate`, porque SQLAlchemy envuelve la excepción del driver.

**Alternativas descartadas**: consultar `Cliente` antes de insertar (prohibido por las reglas duras) y distinguir el caso FK con 404 (descartado por el usuario: se mantiene 409 en todas las altas con FK, diferenciando solo el mensaje).

### D-08 — Infraestructura de pruebas con PostgreSQL real y Alembic

- `requirements-dev.txt` con `pytest`, `pytest-asyncio` y `httpx`; `requirements.txt` de producción no cambia.
- `pyproject.toml` con `[tool.pytest.ini_options]` y `asyncio_mode = "auto"` para no repetir decoradores.
- `test/conftest.py`: lee `TEST_DATABASE_URL` (con `DATABASE_URL` como respaldo), exige driver `postgresql+asyncpg`, crea el motor de prueba y aplica `alembic upgrade head` de forma programática (`alembic.config.Config` + `command.upgrade`) una vez por sesión. Nunca usa `create_all`.
- La dependencia `get_session` se sobrescribe con la fábrica de sesiones de prueba; la app se ejercita con `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`, sin depender del `lifespan`.
- Entre tests se limpian las tablas de dominio con `TRUNCATE ... RESTART IDENTITY CASCADE` (sin tocar `alembic_version`), lo que da aislamiento sin transacciones anidadas entre la app y el test.
- Fixtures auxiliares para crear editorial, género, autor, libro y cliente por API o por sesión, según convenga al caso.

**Alternativas descartadas**: SQLite (no reproduce CHECK/FK/SQLSTATE de PostgreSQL), `create_all` (prohibido), `asgi-lifespan` (dependencia extra no pedida) y transacciones anidadas compartidas (la app abre su propia sesión por petición).

### D-09 — TDD estricto y convivencia con los `.http`

Cada grupo de trabajo arranca con el test que falla, luego el mínimo código para pasarlo y después la triangulación (un autor vs. varios, un renglón vs. varios, camino feliz vs. cada error). Los tests viven en `test/test_*.py` y usan nombres en español coherentes con el resto del repo. Los `test/*.http` se conservan como verificación manual de la consigna; se actualizan sus comentarios de respuesta esperada cuando cambian códigos o mensajes (por ejemplo, libro repetido 409→422).

**Desviación acordada con el usuario**: en esta corrida no hay base PostgreSQL de prueba configurada, así que la verificación funcional se hace con los `.http` y chequeo estático (`py_compile`), y la suite `pytest` se ejecuta después con `TEST_DATABASE_URL`. Los tests se escriben igual, pero sus gates RED/GREEN quedan pendientes de ejecución y así se reporta al cerrar.

**Alternativas descartadas**: escribir primero la implementación y luego los tests (viola el TDD estricto activo) y borrar los `.http` (son entregable de la consigna).

### D-10 — Errores: handler global y mensajes propios

Se reutiliza el handler global `IntegrityError`→409 y `DataError`→422. Los services solo agregan mensajes propios cuando la base no alcanza para distinguir el caso: libro inexistente en la venta (lectura de precio) y cliente inexistente en el perfil (SQLSTATE 23503). Ninguna respuesta incluye nombres de tablas, restricciones, columnas, mensajes del driver ni trazas.

**Alternativas descartadas**: capturar `IntegrityError` en cada service y devolver mensajes específicos (duplicaría lógica y filtraría el motivo interno).

## Risks / Trade-offs

- [La extracción del SQLSTATE puede variar según la versión de SQLAlchemy/asyncpg] → Se implementa un helper que prueba `exc.orig.sqlstate` y `exc.orig.__cause__.sqlstate`; si no lo obtiene, relanza al handler global (409 genérico) en lugar de romper. Los tests contra PostgreSQL real lo verifican.
- [Cambiar 409→422 en libro repetido y 400→422 en venta vacía rompe clientes/.http previos] → Es el comportamiento que exige la consigna; se actualizan los `.http` y se documenta como cambio de contrato en el proposal.
- [`genero_id` obligatorio en el DTO choca con el `.http` de C-04 sin género] → Se actualizan los `.http` de libros para enviar siempre `genero_id`; la columna sigue siendo nullable para no romper datos existentes.
- [Los tests necesitan una base PostgreSQL de prueba disponible] → Se documenta `TEST_DATABASE_URL` en el README y se usa `DATABASE_URL` como respaldo; el esquema se crea solo con Alembic. Por decisión del usuario, en esta corrida la verificación funcional se hace con los `.http` y la suite `pytest` se ejecuta después.
- [Precargar el libro en listados de ventas podría rozar el alcance de C-06] → Solo se precarga lo imprescindible para exponer `titulo` sin `lazy="raise"`; el conteo y la optimización de consultas siguen siendo de C-06.
- [El mensaje global de `IntegrityError` es genérico] → Es un mensaje propio y no filtra texto de la base (RN-12); se acepta que no distinga ISBN de FK en la respuesta.

## Migration Plan

No hay cambios de esquema ni migraciones nuevas. El despliegue es un cambio de código: contratos y services de libros, clientes y ventas, más la infraestructura de tests. Rollback: revertir el commit del change; la base queda intacta (las tablas ya existían) y los `.http` vuelven a su contrato anterior si se revierte también su actualización.

## Open Questions

Ninguna que bloquee. Las decisiones sobre `genero_id` obligatorio, `autores` opcional, respuesta de venta con `cliente_id` y perfil con ruta autoritativa quedan resueltas en D-02, D-06 y D-07; la verificación funcional de esta corrida queda en los `.http` y la suite `pytest` se ejecuta después (D-09).
