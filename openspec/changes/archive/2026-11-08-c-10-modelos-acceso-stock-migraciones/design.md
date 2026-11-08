# Design

> **Governance: CRÍTICO.** Nada de este diseño se implementa sin aprobación humana explícita al iniciar `/opsx:apply`. Además hay dos puntos de control obligatorios durante el apply: (1) mostrar la 0003 autogenerada **antes** de `alembic upgrade`, y (2) mostrar la 0004 escrita a mano **antes** de aplicarla. El usuario aprueba cada una.

## Context

Ver `proposal.md` (Why). Estado observado en `main` (d24637f, C-08 y C-09 ya implementados):

- Alembic vive en **`migrations/`** (no `alembic/` como dice `CHANGES.md`). `migrations/env.py` ya lee la URL de `Settings().database_url` (`POSTGRES_*`) e importa `app.models` como `target_metadata`: **no hace falta tocarlo** para registrar los modelos nuevos; basta con sumarlos al agregador `app/models.py`.
- Cadena actual: `0001` y `0002`, con `revision = '0001'`/`'0002'` (ids cortos, nombres `000N_<slug>.py`) y docstring de revisión manual. Ese es el estilo a seguir.
- `app/core/metadata.py` fija la convención de nombres (`pk_`, `fk_<tabla>_<col>_<ref>`, `uq_<tabla>_<col>`, `ck_<tabla>_<nombre>`, `ix_<col_label>`). Todas las relaciones usan `lazy="raise"`.
- `Libro.isbn` hoy es `Field(unique=True)` → restricción `uq_libro_isbn`. `Libro` no tiene `borrado_en`; `LibroRepository` hereda de `BaseRepository` (su docstring lo dice) aunque `SoftDeleteRepository` ya existe en `app/core/repository.py`.
- Las violaciones de integridad se traducen a 409 con un manejador global genérico (`app/core/errors.py`) y en `clientes/service.py` por SQLSTATE; **nada depende del nombre `uq_libro_isbn`**, así que reemplazarlo no cambia respuestas HTTP.
- `scripts/seed.py` (TP) importa modelos módulo por módulo **sin** `app.models`. Con relaciones nuevas declaradas por nombre (`"Usuario"`, `"MovimientoStock"`), configurar los mappers fallaría si `app.modules.usuarios.models` no se importó.
- No existe runner de pruebas (no hay `pytest`; `CHANGES.md` y `CLAUDE.md` fijan que las pruebas son `.http` + `test/solo_agregado.sql`).
- Los specs principales `migraciones-esquema` y `data-model-conventions` ya mencionan 14 tablas, `DATABASE_URL` y una cabeza `0003_drop_ix_cliente_usuario_id` que no existe en el repo (resto de la reconstrucción de C-03 en 7c8fbb1). Los deltas de este change los alinean con el código real: cabeza `0004`, URL desde `Settings`.

## Goals / Non-Goals

**Goals:**
- Esquema completo del Parcial (14 tablas + trigger) creado solo por Alembic, reversible hasta `base` y sin drift (`alembic check`).
- Modelos con navegación en los dos extremos, todo `lazy="raise"`, nombres deterministas.
- Que lo ya implementado siga funcionando: la app arranca, los `.http` C-01..C-09 siguen dando lo mismo, `scripts/seed.py` sigue cargando.

**Non-Goals:**
- Schemas, repositorios, UoW, servicios o routers de `usuarios` (C-11/C-12); bcrypt, JWT, `intento_acceso` en sesión propia (C-11).
- Usar `borrado_en` en lecturas, `SoftDeleteRepository` en libros, escritura de stock por movimientos, `stock_inicial`, reponer, baja (C-13).
- `seed.py` del Parcial con usuarios y movimientos coherentes (C-14). El `test/solo_agregado.sql` de C-10 es un **borrador** autocontenido; C-14 lo deja final sobre los datos del seed.
- Segundo mecanismo de solo agregado por permisos del rol de base (la consigna lo excluye explícitamente).

## Decisions

### D-01 — Ubicación de los modelos
`Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad` en `app/modules/usuarios/models.py` (crear el paquete con `__init__.py` y solo `models.py`; el resto del módulo es C-11). `MovimientoStock` en `app/modules/libros/models.py`, junto a `Libro` (lo pide la consigna y el spec `data-model-conventions` "Modelos ubicados en su módulo funcional"). Referencias cruzadas con strings + `TYPE_CHECKING`, como los modelos actuales. Cada `models.py` nuevo importa `app.core.metadata` primero.
*Alternativa descartada*: un módulo `stock/` propio → contradice la estructura obligatoria.

### D-02 — Tipos y largos

| Tabla.columna | Tipo | Nulo | Notas |
|---|---|---|---|
| `usuario.email` | VARCHAR(254) | no | `uq_usuario_email` |
| `usuario.nombre` | VARCHAR(120) | no | igual que `cliente.nombre` |
| `usuario.password_hash` | VARCHAR(255) | no | bcrypt da 60; margen para otro esquema sin migrar |
| `usuario.activo` / `debe_cambiar_password` | BOOLEAN | no | default `true` / `false` (Python y `server_default`) |
| `asignacion_rol.rol` | VARCHAR(20) | no | `ck_asignacion_rol_rol_valido` |
| `asignacion_rol.desde` | timestamptz | no | default ahora (UTC) |
| `asignacion_rol.vence_en` / `revocada_en` | timestamptz | sí | |
| `asignacion_rol.usuario_id` / `otorgada_por` | INTEGER FK `usuario.id` | no / sí | ambos con `index=True` |
| `intento_acceso.cuando` | timestamptz | no | default ahora |
| `intento_acceso.email` | VARCHAR(254) | no | sin FK (puede no existir) |
| `intento_acceso.ip` | VARCHAR(45) | no | cabe IPv6 textual |
| `intento_acceso.exito` | BOOLEAN | no | |
| `evento_seguridad.cuando` | timestamptz | no | default ahora |
| `evento_seguridad.actor` | VARCHAR(254) | no | correo o `SISTEMA`; texto, no FK |
| `evento_seguridad.accion` | VARCHAR(255) | no | |
| `movimiento_stock.libro_id` / `usuario_id` | INTEGER FK | no | `index=True` |
| `movimiento_stock.venta_id` | INTEGER FK `venta.id` | sí | `index=True` |
| `movimiento_stock.cantidad` | INTEGER | no | `ck_movimiento_stock_cantidad_no_cero` (`cantidad <> 0`) |
| `movimiento_stock.motivo` | VARCHAR(120) | no | "Stock inicial", "Reposición", "Venta N" |
| `movimiento_stock.cuando` | timestamptz | no | default ahora |
| `libro.borrado_en` | timestamptz | sí | |
| `cliente.usuario_id` | INTEGER FK `usuario.id` | sí | `unique=True`, **sin** `index=True` (el UNIQUE lo cubre) |

Fechas con `sa_type=DateTime(timezone=True)` y `default_factory=lambda: datetime.now(UTC)` (patrón de `Venta.fecha`). Para `cuando`/`desde` y las banderas se agrega también `server_default` (`now()`, `true`, `false`) para que las inserciones directas en `psql` (`solo_agregado.sql`) funcionen; `alembic check` no compara `server_default` por defecto, así que no genera drift. FK sin `ondelete`: un borrado en cascada sobre `movimiento_stock` chocaría con el trigger, y la consigna nunca borra libros ni ventas.

### D-03 — Índices únicos parciales con nombre explícito
En `__table_args__`:
- `Libro`: `Index("ix_libro_isbn_vigente", "isbn", unique=True, postgresql_where=text("borrado_en IS NULL"))`, y `isbn` deja de tener `unique=True`.
- `AsignacionRol`: `Index("ix_asignacion_rol_abierta", "usuario_id", "rol", unique=True, postgresql_where=text("revocada_en IS NULL"))`.
- `IntentoAcceso`: `Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando")`.

Nombre explícito porque la convención `ix_%(column_0_label)s` daría `ix_libro_isbn` / `ix_asignacion_rol_usuario_id`, este último en conflicto con el índice simple de la FK.
*Alternativa descartada*: `UniqueConstraint` parcial → PostgreSQL no admite `WHERE` en restricciones UNIQUE, solo en índices.

### D-04 — Relaciones (todas `lazy="raise"`, `back_populates` en los dos extremos)
- `Usuario.asignaciones` ↔ `AsignacionRol.usuario` con `foreign_keys` explícito (`AsignacionRol.usuario_id`), y `Usuario.asignaciones_otorgadas` ↔ `AsignacionRol.otorgante` (`AsignacionRol.otorgada_por`): hay dos FK a `usuario` y sin `foreign_keys` SQLAlchemy no sabe cuál usar.
- `Usuario.cliente` ↔ `Cliente.usuario`, ambos `uselist=False` (objeto, no lista).
- `Usuario.movimientos`, `Libro.movimientos`, `Venta.movimientos` ↔ `MovimientoStock.usuario/libro/venta`. Sin `cascade` de borrado (solo agregado). `Venta.movimientos` es la única línea que toca `app/modules/ventas/models.py`.
- `IntentoAcceso` y `EventoSeguridad` sin relaciones.

### D-05 — `movimiento_stock.usuario_id` obligatorio
La consigna marca "(nulo)" solo en `venta_id`; `usuario_id` queda NOT NULL. Consecuencia: no se pueden crear movimientos sin un usuario existente (ver D-08).

### D-06 — Migración 0003 autogenerada
`alembic revision --autogenerate --rev-id 0003 -m "acceso movimientos y baja logica"` sobre una base en `0002`. Revisión manual esperada (y a anotar en el docstring):
1. Que aparezcan `drop_constraint('uq_libro_isbn')` y `create_index('ix_libro_isbn_vigente', …, unique=True, postgresql_where=…)`. Alembic no compara la cláusula `WHERE` de los índices: si el autogenerate la omite o la deja mal, `alembic check` no lo detecta, así que se verifica a mano en el archivo y luego en `pg_indexes`.
2. Orden de creación: `usuario` antes de `asignacion_rol`, `movimiento_stock` y de la FK de `cliente.usuario_id`; `movimiento_stock` después de `libro` y `venta` (ya existen).
3. Que no aparezca un `ix_cliente_usuario_id` duplicando el UNIQUE.
4. `downgrade` en orden inverso: FK/UNIQUE de `cliente`, `movimiento_stock`, `evento_seguridad`, `intento_acceso`, `asignacion_rol`, `usuario`; quitar `ix_libro_isbn_vigente`, recrear `uq_libro_isbn`, quitar `borrado_en`.
5. Sin migración de datos (ver D-08).

### D-07 — Migración 0004 escrita a mano
`alembic revision --rev-id 0004 -m "trigger solo agregado movimiento stock"` (sin autogenerate). `upgrade` con `op.execute`:
- Función `movimiento_stock_solo_agregado()` en PL/pgSQL que hace `RAISE EXCEPTION 'movimiento_stock es de solo agregado: % no permitido', TG_OP;` (SQLSTATE por defecto `P0001`).
- Trigger `tg_movimiento_stock_solo_agregado BEFORE UPDATE OR DELETE ON movimiento_stock FOR EACH ROW EXECUTE FUNCTION movimiento_stock_solo_agregado();`.
- `downgrade`: `DROP TRIGGER IF EXISTS …` y `DROP FUNCTION IF EXISTS …`.

`TRUNCATE` **no** se bloquea: la consigna pide UPDATE y DELETE, y el `seed.py` del Parcial (C-14) necesita vaciar la tabla; deberá hacerlo con `TRUNCATE … RESTART IDENTITY CASCADE`, nunca con `DELETE`. Por fila (no por sentencia) porque es la forma estándar y deja intactas las filas; un `UPDATE` sin filas afectadas no falla, lo que no viola RN-12.
*Alternativa descartada*: `REVOKE UPDATE, DELETE` al rol de la app → la consigna lo deja fuera (un solo rol de base).

### D-08 — Datos existentes e invariante de stock (IN-05, SU-13)
0003 **no** inserta movimientos "Stock inicial": `usuario_id` es obligatorio y al migrar no hay usuarios. Se adopta SU-13: la base del Parcial se reconstruye con el `seed.py` de C-14, que carga usuarios y movimientos coherentes. Entre C-10 y C-13 el stock se sigue escribiendo como en el TP y la invariante `stock = Σ movimientos` no se exige todavía. Queda escrito en el docstring de 0003.

### D-09 — Conexión mínima con lo ya implementado
- `app/models.py`: agregar los 5 modelos al import y a `__all__` (único archivo compartido con C-09, ya integrado).
- `scripts/seed.py`: agregar `import app.models` para que los mappers resuelvan `"Usuario"`/`"MovimientoStock"` (si no, el seed del TP rompe). Es la única línea que se le toca; su contenido lo reemplaza C-14.
- `migrations/env.py`: sin cambios (ya importa `app.models`); solo se verifica.
- Schemas de libros: `LibroRead` es explícito, así que `borrado_en` no aparece en respuestas hasta que C-13 lo decida.

### D-10 — Pruebas y verificación (sin runner: Strict TDD no aplica)
No hay runner automático, así que el ciclo RED/GREEN se reemplaza por verificaciones ejecutables que se corren antes y después:
- `test/solo_agregado.sql` (borrador, autocontenido): `BEGIN`; inserta un usuario y un movimiento sobre un libro existente; `SAVEPOINT` + `UPDATE` → error; `ROLLBACK TO SAVEPOINT`; `SAVEPOINT` + `DELETE` → error; `ROLLBACK`. Cada sentencia con su resultado esperado comentado. Se corre en `0003` (UPDATE/DELETE **aceptados**: "rojo") y en `0004` (rechazados: "verde").
- `test/C-10-esquema.http`: regresión del ISBN repetido entre vigentes (409, mensaje propio) y `GET /health/ready` 200 con el esquema nuevo.
- Verificación de esquema por `psql` (registrada en `tasks.md`, no como archivo de prueba): `\d` de las tablas, `pg_indexes`, `information_schema.columns`, inserts que violan CHECK/UNIQUE/FK.
- Ciclo `upgrade head → downgrade base → upgrade head` y `alembic check`.
- Regresión: los `.http` C-01..C-09 existentes tras `python scripts/seed.py`.

### D-11 — Skills a cargar en el apply
`sqlmodel` (modelos, relaciones con dos FK), `postgresql-table-design` (índices parciales, timestamptz, trigger), `database-patterns` (Alembic y migraciones reversibles), `python-backend` (SQLAlchemy 2 async en `env.py`). Para dudas de API puntual (`postgresql_where` en autogenerate, `foreign_keys` en SQLModel) consultar context7.

## Risks / Trade-offs

- [El autogenerate no detecta bien el cambio UNIQUE → índice parcial, o pierde el `WHERE`] → revisión obligatoria del archivo (punto de control 1) y verificación en `pg_indexes`; corregir a mano y explicarlo en el docstring.
- [`downgrade` de 0003 falla si hay dos libros con el mismo ISBN (uno dado de baja), porque recrea `uq_libro_isbn`] → aceptado; el ciclo exigido es sobre base vacía. Se anota en el docstring.
- [`server_default` divergente del default de Python] → ambos representan lo mismo (`now()` / UTC, `true`/`false`); `alembic check` no los compara.
- [Entrypoints que importan modelos sueltos sin el agregador fallan al configurar mappers] → `scripts/seed.py` importa `app.models` (D-09); `main.py` y `env.py` ya lo hacen.
- [Un `UPDATE` accidental sobre `movimiento_stock` desde la app daría `InternalError` (500) en vez de 409] → ningún código del Parcial actualiza movimientos (C-13 solo inserta); se documenta para C-13.
- [Conflicto con C-09 en `app/models.py`] → C-09 ya está en `main`; C-10 solo agrega líneas.
- [Los specs principales tenían datos que no coinciden con el repo (cabeza `0003_drop_ix_cliente_usuario_id`, `DATABASE_URL`)] → los deltas MODIFIED los corrigen al archivar.

## Migration Plan

1. Base de trabajo en `0002` con datos del TP (`python scripts/seed.py`).
2. Modelos + agregador → `alembic revision --autogenerate --rev-id 0003` → **revisión humana** → `alembic upgrade head`.
3. Correr `test/solo_agregado.sql` (UPDATE/DELETE aceptados en 0003).
4. Escribir 0004 → **revisión humana** → `alembic upgrade head` → `solo_agregado.sql` (rechazados).
5. `alembic check`; `downgrade -1` + `upgrade head`; sobre base vacía `upgrade head → downgrade base → upgrade head`.
6. Regresión `.http` C-01..C-09 y `test/C-10-esquema.http`.

Rollback: `alembic downgrade 0002` deja el esquema del TP (salvo el caso de ISBN duplicados entre bajas, imposible antes de C-13).

## Open Questions

- Mensaje y SQLSTATE exactos del trigger: se usa `P0001` con texto propio; si la cátedra espera otro código, se cambia solo en 0004 sin afectar specs.
- Textos de `motivo` normalizados ("Stock inicial", "Reposición", "Venta N"): los fija C-13/C-14; en C-10 la columna es texto libre.
