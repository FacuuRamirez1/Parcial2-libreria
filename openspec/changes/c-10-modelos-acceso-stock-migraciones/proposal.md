# Proposal

> **Governance: CRÍTICO** (migraciones, trigger de solo agregado, tablas de seguridad). Este change produce solo artefactos de planificación. El `/opsx:apply` requiere **aprobación humana explícita** antes de escribir cualquier línea de código, migración o prueba, y cada migración generada se presenta para revisión antes de aplicarla.

## Why

El esquema actual es el del TP caps 1-4: 9 tablas en la cadena `0001 → 0002`, sin usuarios, roles, intentos de acceso, historial de seguridad ni movimientos de stock; `libro.isbn` tiene un `UNIQUE` común y no hay borrado lógico. El Ejercicio 2 del Parcial (10 pts) y el trigger del Ejercicio 7 (RN-12) piden los modelos nuevos, los cambios a `cliente` y `libro`, y dos migraciones más (0003 autogenerada, 0004 a mano). Sin este esquema no pueden construirse la autenticación (C-11), la autorización (C-12) ni el stock por movimientos y la baja lógica (C-13).

## What Changes

- **Módulo `usuarios` (solo modelos)**: `app/modules/usuarios/models.py` con `Usuario`, `AsignacionRol`, `IntentoAcceso` y `EventoSeguridad` (nombres de tabla y columna exactos de la consigna). `usuario.email` UNIQUE, sin columna `rol`; `asignacion_rol` con CHECK de rol (`ADMIN`, `VENDEDOR`, `CLIENTE`) e **índice único parcial** `(usuario_id, rol) WHERE revocada_en IS NULL` (RN-03); índice `(email, ip, cuando)` en `intento_acceso`; `evento_seguridad.actor` es texto, no FK. El resto del módulo (schemas, repository, UoW, service, router) es C-11.
- **`MovimientoStock` en `app/modules/libros/models.py`**: `movimiento_stock` con `libro_id`, `venta_id` (nulo), `usuario_id`, `cantidad` (CHECK `<> 0`), `motivo`, `cuando`; índice en las tres FK; navegación en los dos extremos (`Libro`, `Venta`, `Usuario`).
- **`libro` (cambia)**: se agrega `borrado_en` (`timestamptz`, nulo). **BREAKING (esquema)**: el `UNIQUE(isbn)` (`uq_libro_isbn`) se **reemplaza** por un índice único parcial `(isbn) WHERE borrado_en IS NULL` (RN-01, DD-09). Siguen los CHECK de precio y stock.
- **`cliente` (cambia)**: se agrega `usuario_id` (FK a `usuario`, nulo, UNIQUE); `Cliente.usuario` devuelve un objeto. `email` sigue UNIQUE.
- **Agregador `app/models.py`**: importa los 5 modelos nuevos (14 tablas). `migrations/env.py` ya importa `app.models` y lee la URL de `Settings`: no requiere cambios salvo que la revisión lo detecte.
- **Migración 0003** (`alembic revision --autogenerate --rev-id 0003`): tablas de acceso, `movimiento_stock`, `cliente.usuario_id`, `libro.borrado_en` y reemplazo del UNIQUE del ISBN; **leída y comentada a mano antes de aplicarla** (índices parciales, nombres, orden del `downgrade`).
- **Migración 0004** (escrita a mano, `--rev-id 0004`): función PL/pgSQL + trigger `BEFORE UPDATE OR DELETE` sobre `movimiento_stock` que rechaza la operación (RN-12); `downgrade` elimina trigger y función.
- **Verificación**: `upgrade head` sobre base vacía → `downgrade base` → `upgrade head`; `alembic check` sin drift.
- **Pruebas**: borrador de `test/solo_agregado.sql` (UPDATE y DELETE rechazados por el trigger, caso C-14) y `test/C-10-esquema.http` (regresión: ISBN repetido entre vigentes sigue en 409 con mensaje propio).

## Capabilities

### New Capabilities

- `access-data`: tablas `usuario`, `asignacion_rol`, `intento_acceso` y `evento_seguridad` con sus restricciones, índices y navegación (sin lógica de autenticación ni autorización).
- `stock-movements-data`: tabla `movimiento_stock`, su CHECK, índices y navegación, y la garantía de solo agregado impuesta por el trigger de la base.

### Modified Capabilities

- `catalog-data`: `libro.isbn` pasa de UNIQUE común a único solo entre vigentes; se agrega `libro.borrado_en`.
- `customer-data`: se agrega `cliente.usuario_id` (nulo, UNIQUE, FK) y la navegación `Cliente.usuario` como objeto.
- `migraciones-esquema`: la cadena pasa a `0001 → 0004` con cabeza `0004`; la URL de Alembic sale de `Settings` (`POSTGRES_*`), ya no de `DATABASE_URL`; ciclo `upgrade head → downgrade base → upgrade head`; comentario de revisión obligatorio en 0003 y 0004.
- `data-model-conventions`: el índice por FK abarca las FK nuevas; la restricción que respalda el caso de ISBN repetido deja de ser `uq_libro_isbn` y pasa a ser el índice único parcial; fechas nuevas `timestamptz`.

## Impact

- **Código nuevo**: `app/modules/usuarios/__init__.py`, `app/modules/usuarios/models.py`, `migrations/versions/0003_*.py`, `migrations/versions/0004_*.py`, `test/solo_agregado.sql` (borrador), `test/C-10-esquema.http`.
- **Código modificado**: `app/modules/libros/models.py` (C-02: `borrado_en`, índice parcial, `MovimientoStock`, `Libro.movimientos`), `app/modules/clientes/models.py` (C-02: `usuario_id`, `Cliente.usuario`), `app/modules/ventas/models.py` (`Venta.movimientos`, solo navegación), `app/models.py` (agregador), `scripts/seed.py` (una línea: `import app.models`, para que los mappers resuelvan las relaciones nuevas).
- **Intactos**: `migrations/versions/0001_*` y `0002_*`; servicios, routers y repositorios (la baja lógica y el `SoftDeleteRepository` en libros los conecta C-13; el alta de cliente con `usuario_id`, C-11).
- **API**: ningún endpoint nuevo ni cambio de contrato. El 409 por ISBN repetido entre vigentes se conserva.
- **Base de datos**: 5 tablas nuevas, 2 columnas nuevas, reemplazo de `uq_libro_isbn`, 1 función y 1 trigger.
- **Dependencias**: ninguna nueva.
- **Coordinación con C-09** (en paralelo, ya en `main` en d24637f): C-10 no toca `repository.py`/`service.py`/`router.py` de ningún módulo; el único archivo compartido es `app/models.py`.
