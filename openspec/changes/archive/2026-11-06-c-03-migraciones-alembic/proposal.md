# Proposal: C-03 — Migraciones Alembic (reconstrucción de archivo)

## Why

C-03 (`migraciones-alembic`) se implementó en el commit `7a37936`, pero nunca se archivó como change de OpenSpec. `CHANGES.md` lo marca `[x]` y el repositorio quedó con 6 carpetas de archivo para 7 changes, un desfase de trazabilidad detectado en la auditoría final. Esta reconstrucción documenta con evidencia el estado realmente entregado, sin modificar código ni esquema.

## What Changes

- Se reconstruyen `proposal.md`, `design.md`, `tasks.md` y delta specs de C-03.
- Se documenta la migración `0001_modelos_acceso_y_stock` (14 tablas: las 9 de la consigna más 5 de infraestructura de acceso/stock), la migración `0002_trigger_movimiento_stock` y la corrección posterior `0003_drop_ix_cliente_usuario_id`.
- Se corrige el inventario de `data-model-conventions`: el metadata tiene 14 tablas, no 9; las 5 adicionales son `usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad` y `movimiento_stock`.
- Se deja constancia de que `scripts/seed.py`, previsto originalmente en C-03, se completó en C-07.

## Impact

- Solo documentación OpenSpec: `openspec/changes/...` y `openspec/specs/...`.
- Sin cambios de código, tests, migraciones ni esquema.
- El change se archiva para completar 7/7 changes del roadmap.
