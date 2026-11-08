# Tasks: C-07 — Asincronía sin bloqueos y cierre operativo

## 1. Preparación

- [x] 1.1 Crear el change `c-07-asincronia-sin-bloqueos` con proposal, design y delta specs.
- [x] 1.2 Registrar la línea base: `python -m pytest -q` en verde antes de tocar código.

## 2. Aviso de comprobante en segundo plano (TDD)

- [x] 2.1 RED: agregar `test/test_asincronia_ventas.py` con (a) el aviso registra id/total en el log y el POST dura al menos 0.5 s, (b) una petición concurrente responde mientras el aviso duerme, (c) auditoría estática sin bloqueos. Ejecutar y confirmar los fallos esperados.
- [x] 2.2 GREEN: agregar `enviar_aviso_comprobante` y `_esperar_aviso` en `app/modules/ventas/service.py`; inyectar `BackgroundTasks` y agendar la tarea en `POST /ventas/`.
- [x] 2.3 TRIANGULAR: cubrir el caso de varios renglones (total compuesto) y verificar que el aviso usa el total persistido.
- [x] 2.4 REFACTOR: extraer el armado del payload de la venta en el test si se repite; mantener verdes las pruebas.

## 3. Auditoría de asincronía

- [x] 3.1 Confirmar que `app/` no usa `time.sleep`, `requests` ni sesiones síncronas (test estático).
- [x] 3.2 Documentar en el README que el aviso corre después de la respuesta y no bloquea el event loop.

## 4. Seed reproducible

- [x] 4.1 RED: `test/test_seed.py` ejecuta `scripts/seed.py` dos veces contra la base de test y verifica catálogo completo sin duplicados.
- [x] 4.2 GREEN: implementar `scripts/seed.py` asincrónico, idempotente, con `DATABASE_URL`, sin `create_all`.
- [x] 4.3 Ejecutar el seed manualmente contra una base migrada y verificar el resumen.

## 5. README y `.http` finales

- [x] 5.1 Reescribir `README.md` desde cero: requisitos, PostgreSQL, venv, dependencias, `.env`, `alembic upgrade head`, seed, arranque, endpoints, tests, estructura y reglas.
- [x] 5.2 Agregar a `test/ventas.http` la evidencia del aviso en segundo plano (log a los 0.5 s).
- [x] 5.3 Verificar el mapa de `.http` para los casos C-01 a C-08.

## 6. Cierre

- [x] 6.1 Ejecutar la suite completa (`python -m pytest -q`) y registrar el total.
- [x] 6.2 Ejecutar `openspec validate --all --strict` y registrar el total.
- [x] 6.3 Archivar el change, actualizar `CHANGES.md` con C-07 `[x]` y el resumen.
