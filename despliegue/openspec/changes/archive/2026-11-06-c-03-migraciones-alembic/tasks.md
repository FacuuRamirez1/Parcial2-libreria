# Tasks: C-03 — Migraciones Alembic (reconstrucción de archivo)

## 1. Reconstrucción documental

- [x] 1.1 Reconstruir `proposal.md`, `design.md` y delta specs a partir del estado real del repositorio (commit `7a37936`).
- [x] 1.2 Documentar la desviación del plan original: `0001` incluye el metadata completo y `0002` crea el trigger de stock, no la tabla `genero`.

## 2. Configuración de Alembic

- [x] 2.1 Verificar `alembic.ini` sin `sqlalchemy.url` ni credenciales, con `script_location` y `prepend_sys_path`.
- [x] 2.2 Verificar `migrations/env.py` asincrónico: `load_dotenv`, `DATABASE_URL`, `async_engine_from_config`, `NullPool`, `target_metadata = SQLModel.metadata`.

## 3. Migraciones

- [x] 3.1 Documentar `0001_modelos_acceso_y_stock`: 14 tablas, restricciones, índices y el índice único parcial de ISBN.
- [x] 3.2 Documentar `0002_trigger_movimiento_stock`: función y trigger que bloquean UPDATE/DELETE en `movimiento_stock`.
- [x] 3.3 Documentar `0003_drop_ix_cliente_usuario_id` como corrección posterior de drift y cabeza actual.

## 4. Verificación

- [x] 4.1 `alembic upgrade head` sobre base vacía: OK.
- [x] 4.2 `alembic downgrade -1` y `alembic upgrade head`: OK; vuelve a `0003_drop_ix_cliente_usuario_id`.
- [x] 4.3 `alembic check`: “No new upgrade operations detected”.
- [x] 4.4 `python -m pytest -q`: 69 tests en verde.

## 5. Cierre

- [x] 5.1 Corregir el inventario de `data-model-conventions` a 9 tablas de la consigna + 5 de infraestructura (14 total).
- [x] 5.2 Dejar constancia de que `scripts/seed.py` se completó en C-07, no en C-03.
- [x] 5.3 Archivar el change y completar 7/7 changes del roadmap.
