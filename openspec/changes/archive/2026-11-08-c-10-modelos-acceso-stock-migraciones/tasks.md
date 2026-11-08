# Tasks

> **Governance: CRÍTICO.** Antes de la tarea 1.1 el `/opsx:apply` necesita **aprobación humana explícita** para escribir código. Hay además dos puntos de control con aprobación: la 0003 generada (tarea 3.2) y la 0004 escrita (tarea 4.2), cada una mostrada **antes** de `alembic upgrade`.
> **Skills a cargar antes de escribir**: `sqlmodel`, `postgresql-table-design`, `database-patterns`, `python-backend` (context7 para dudas puntuales de `postgresql_where`/`foreign_keys`).
> **Pruebas**: no hay runner (sin pytest, regla del proyecto) → Strict TDD no aplica; el equivalente RED/GREEN es correr `test/solo_agregado.sql` en 0003 (acepta) y en 0004 (rechaza), más verificaciones por `psql` y `.http`. Ver `design.md` D-10.
> **Reglas duras**: sin `create_all`; 0001 y 0002 intactas; sin carga perezosa (`lazy="raise"`); fechas nuevas `timestamptz`; índice por FK nueva; solo se agregan columnas; no commitear sin orden del usuario. Alembic está en `migrations/` (no `alembic/`).

## 0. Línea de base

- [x] 0.1 Con PostgreSQL 16 y `.env` (`POSTGRES_*`, `JWT_SECRET_KEY`) en la base de trabajo: `alembic upgrade head` (debe quedar en `0002`), `python scripts/seed.py`, levantar la app y correr los `.http` C-01..C-09; anotar el resultado como línea de base. Si algo ya falla, detenerse y reportarlo como falla previa. Verificación: `alembic current` = `0002` y la lista de casos que pasan queda anotada.

## 1. Modelos de acceso (módulo usuarios)

- [x] 1.1 Crear `app/modules/usuarios/__init__.py` y `app/modules/usuarios/models.py` con `Usuario` (sin columna `rol`, `uq_usuario_email`, banderas con default Python y `server_default`) según `design.md` D-01/D-02 y spec `access-data`. Verificación: `python -c "import app.modules.usuarios.models"` termina sin error y sin conectarse a la base.
- [x] 1.2 Agregar `AsignacionRol` con CHECK `rol IN ('ADMIN','VENDEDOR','CLIENTE')`, `usuario_id`/`otorgada_por` con índice, fechas `timestamptz`, e índice único parcial `ix_asignacion_rol_abierta` (D-03); relaciones `usuario`/`otorgante` con `foreign_keys` explícito (D-04). Verificación: compilar el DDL (`CreateTable`/`CreateIndex` con dialecto postgresql) y ver el CHECK, los dos índices de FK y `CREATE UNIQUE INDEX ix_asignacion_rol_abierta … WHERE revocada_en IS NULL`.
- [x] 1.3 Agregar `IntentoAcceso` (índice `ix_intento_acceso_email_ip_cuando`, sin FK) y `EventoSeguridad` (`actor` texto, sin FK). Verificación: DDL compilado sin claves foráneas y con el índice `(email, ip, cuando)` en ese orden.

## 2. Cambios en libros, clientes y ventas

- [x] 2.1 En `app/modules/libros/models.py`: agregar `Libro.borrado_en` (`timestamptz`, nulo), quitar `unique=True` de `isbn` y declarar `ix_libro_isbn_vigente` (único parcial, `borrado_en IS NULL`) (spec `catalog-data`, D-03). Verificación: DDL de `libro` sin `uq_libro_isbn`, con `borrado_en TIMESTAMP WITH TIME ZONE` y el índice parcial; siguen `ck_libro_precio_positivo` y `ck_libro_stock_no_negativo`.
- [x] 2.2 En el mismo archivo, agregar `MovimientoStock` (`cantidad <> 0`, tres FK con índice, `venta_id` nulo, `usuario_id` obligatorio, sin `ondelete`) y `Libro.movimientos` (spec `stock-movements-data`, D-02/D-04/D-05). Verificación: DDL con `ck_movimiento_stock_cantidad_no_cero` y `ix_movimiento_stock_libro_id`/`_venta_id`/`_usuario_id`.
- [x] 2.3 En `app/modules/clientes/models.py`: `Cliente.usuario_id` (FK, nulo, `unique=True`, sin `index=True`) y `Cliente.usuario` ↔ `Usuario.cliente` con `uselist=False` (spec `customer-data`). En `app/modules/ventas/models.py`: solo `Venta.movimientos`. Verificación: DDL de `cliente` con `uq_cliente_usuario_id` y `fk_cliente_usuario_id_usuario` y sin `ix_cliente_usuario_id`.
- [x] 2.4 Agregar los 5 modelos a `app/models.py` (import + `__all__`) y `import app.models` en `scripts/seed.py` (D-09). Verificación: en un intérprete nuevo, `import app.models; from sqlalchemy.orm import configure_mappers; configure_mappers()` sin error y `len(SQLModel.metadata.tables) == 14`; acceder a `Libro.movimientos` sin precarga sobre un objeto cargado lanza error de `lazy="raise"`.
- [x] 2.5 Confirmar que `migrations/env.py` no necesita cambios (ya importa `app.models` y usa `Settings`) y que `LibroRead` no expone `borrado_en`. Verificación: `alembic heads` responde `0002` sin error de importación; lectura de `app/modules/libros/schemas.py`.

## 3. Migración 0003 (autogenerada)

- [x] 3.1 Con la base en `0002`: `alembic revision --autogenerate --rev-id 0003 -m "acceso movimientos y baja logica"`. Verificación: existe `migrations/versions/0003_acceso_movimientos_y_baja_logica.py` con `down_revision = '0002'`.
- [x] 3.2 **Punto de control (aprobación humana)**: leer la 0003 completa y revisar los 5 puntos de `design.md` D-06 (drop `uq_libro_isbn` + índice parcial con `postgresql_where`, orden de creación, sin `ix_cliente_usuario_id` duplicado, `downgrade` inverso que recrea `uq_libro_isbn`, sin migración de datos); corregir a mano lo que falle y escribir el docstring "generada con --autogenerate, leída antes de aplicar, se corrigió X porque Y" (o "no hizo falta corregir") incluyendo la nota de SU-13 y del downgrade con ISBN duplicados. Mostrarla al usuario y esperar su aprobación. Verificación: el usuario aprueba el archivo; el docstring cumple el spec `migraciones-esquema` "Migraciones nuevas revisadas y documentadas".
- [x] 3.3 `alembic upgrade head` y verificar en `psql`: 14 tablas; `pg_indexes` muestra `ix_libro_isbn_vigente` y `ix_asignacion_rol_abierta` con su `WHERE`; `information_schema.columns` da `timestamp with time zone` en las 7 fechas nuevas; libros y clientes del TP conservan sus datos con `borrado_en`/`usuario_id` nulos. Verificación: salida de las consultas coincide con specs `access-data`, `catalog-data`, `customer-data` y `data-model-conventions`.
- [x] 3.4 Rechazos de restricciones por `psql` dentro de `BEGIN … ROLLBACK`: correo de usuario repetido, rol `SUPERVISOR`, segunda asignación abierta del mismo rol (y aceptación tras revocar), `cantidad = 0`, FK de libro inexistente, dos clientes con el mismo `usuario_id`, ISBN repetido entre vigentes rechazado y aceptado si el otro tiene `borrado_en`. Verificación: cada sentencia falla o pasa según los escenarios de los specs.
- [x] 3.5 Escribir el borrador `test/solo_agregado.sql` (autocontenido según D-10, resultado esperado comentado en cada sentencia) y correrlo con `psql -f` en `0003`. Verificación ("rojo"): UPDATE y DELETE se **aceptan** (todavía no hay trigger) y el script termina en `ROLLBACK` sin dejar filas.

## 4. Migración 0004 (a mano: trigger de solo agregado)

- [x] 4.1 `alembic revision --rev-id 0004 -m "trigger solo agregado movimiento stock"` (sin autogenerate) y escribir `upgrade` (función `movimiento_stock_solo_agregado()` + trigger `tg_movimiento_stock_solo_agregado BEFORE UPDATE OR DELETE … FOR EACH ROW`) y `downgrade` (`DROP TRIGGER IF EXISTS`, `DROP FUNCTION IF EXISTS`) según D-07, con docstring "escrita a mano, leída antes de aplicar, la comparación automática no ve funciones ni triggers; TRUNCATE no se bloquea (seed de C-14)". Verificación: `down_revision = '0003'`; `alembic heads` = `0004`.
- [x] 4.2 **Punto de control (aprobación humana)**: mostrar la 0004 al usuario y esperar su aprobación antes de aplicarla. Verificación: aprobación registrada.
- [x] 4.3 `alembic upgrade head` y correr `test/solo_agregado.sql`. Verificación ("verde"): UPDATE y DELETE fallan con "movimiento_stock es de solo agregado"; el INSERT se acepta; las filas quedan intactas (spec `stock-movements-data` "Movimientos de solo agregado").
- [x] 4.4 `alembic downgrade -1` → `solo_agregado.sql` acepta UPDATE/DELETE → `alembic upgrade head` → los vuelve a rechazar. Verificación: escenario "Revertir solo el trigger" del spec `migraciones-esquema`.

## 5. Ciclo completo, drift y regresión

- [x] 5.1 Sobre una base **vacía**: `alembic upgrade head` → `alembic downgrade base` (sin tablas del dominio ni función del trigger) → `alembic upgrade head` (cabeza `0004`). Verificación: las tres terminan sin error; `\dt` y `\df movimiento_stock_solo_agregado` confirman el estado intermedio.
- [x] 5.2 `alembic check` contra la base en `0004`. Verificación: "No new upgrade operations detected".
- [x] 5.3 Comprobar que 0001 y 0002 no cambiaron y que no hay `create_all`. Verificación: `git diff --stat migrations/versions/0001* migrations/versions/0002*` vacío; búsqueda de `create_all` en `app/`, `scripts/`, `test/` sin resultados.
- [x] 5.4 Escribir `test/C-10-esquema.http` (ISBN repetido entre vigentes → 409 con mensaje propio, sin texto de la base; `GET /health/ready` → 200) con la respuesta esperada comentada, y correrlo tras `python scripts/seed.py`. Verificación: las respuestas coinciden con los comentarios.
- [x] 5.5 Regresión: `python scripts/seed.py` sobre la base en `0004` y los `.http` C-01..C-09. Verificación: mismos resultados que la línea de base de 0.1.

## Workflow follow-up

- Revisión humana del diff completo antes de cualquier commit (el commit solo con orden explícita del usuario; mensaje convencional `feat:`).
- `/opsx:archive c-10-modelos-acceso-stock-migraciones` y marcar C-10 `[x]` en `CHANGES.md`; al archivar, los deltas corrigen en los specs principales la cabeza (`0004`) y la URL desde `Settings`.
- C-11 usa los modelos de `usuarios`; C-13 conecta `borrado_en` con `SoftDeleteRepository` y escribe stock solo por movimientos; C-14 deja final `test/solo_agregado.sql` sobre el seed del Parcial y vacía con `TRUNCATE`.
