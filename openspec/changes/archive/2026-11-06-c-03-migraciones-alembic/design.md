# Design: C-03 — Migraciones Alembic (reconstrucción de archivo)

## Estado observado

- `alembic.ini` no contiene URL: `sqlalchemy.url =` queda vacío y `script_location = %(here)s/migrations`.
- `migrations/env.py` carga `.env` con `load_dotenv(..., override=False)`, exige `DATABASE_URL` y usa `async_engine_from_config` con `NullPool`.
- `target_metadata` es `SQLModel.metadata`, poblado por `import app.models`.
- Cadena actual: `0001_modelos_acceso_y_stock` → `0002_trigger_movimiento_stock` → `0003_drop_ix_cliente_usuario_id` (head).
- `0001` crea 14 tablas: las 9 de la consigna más `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`.
- `0002` crea la función y el trigger `trg_movimiento_stock_solo_agregado`, que rechaza UPDATE y DELETE sobre `movimiento_stock`.
- `0003` elimina el índice no único redundante `ix_cliente_usuario_id` (corrección posterior de drift, no forma parte del alcance original de C-03).

## D-01 — Reconstrucción retroactiva

El archivo documenta lo que efectivamente existe en el repositorio, no el plan original. Se marca como reconstrucción para no fingir que el change se archivó en su momento.

## D-02 — Configuración asincrónica sin secretos

La URL se resuelve en tiempo de ejecución desde `DATABASE_URL` (entorno o `.env`). `alembic.ini` no versiona credenciales y `env.py` falla con un mensaje que nombra la variable si falta.

## D-03 — Una sola migración inicial, no dos

El plan original de C-03 preveía una `0001` sin `genero` y una `0002` que lo agregara. La implementación real autogeneró `0001` con el metadata completo (incluido `genero` y `libro.genero_id`). La `0002` real no agrega género: crea el trigger de solo-agregado de stock. Se documenta la desviación para que la historia coincida con el código.

## D-04 — Trigger de stock

El trigger y su función se crean y eliminan en `upgrade`/`downgrade` con SQL explícito. Bloquea UPDATE y DELETE con un mensaje propio, sin exponer nombres internos.

## D-05 — Corrección de inventario

`data-model-conventions` afirmaba que el metadata contenía exactamente 9 tablas. La realidad verificada es 14. La delta modifica el requisito para distinguir las 9 tablas de la consigna de las 5 de infraestructura, y actualiza el agregador único a 14 modelos. No se elimina ninguna tabla ni se cambia el esquema.

## D-06 — Seed diferido

`scripts/seed.py` figuraba en el scope original de C-03, pero se implementó en C-07. La especificación de C-03 no lo reclama; queda documentado en el archivo de C-07.

## Verificación

- `alembic check` → “No new upgrade operations detected”.
- Ciclo en base temporal: `upgrade head` → `downgrade -1` → `upgrade head` → OK.
- `python -m pytest -q` → 69 tests.
- `openspec validate --all --strict` → 24/24 antes de esta reconstrucción; 25/25 después de agregar `migraciones-esquema`.
