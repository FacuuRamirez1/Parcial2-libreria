# Proposal: C-07 — Asincronía sin bloqueos y cierre operativo

## Why

La consigna (US-010) pide que, al registrar una venta, se agende con `BackgroundTasks` un aviso simulado (`await asyncio.sleep(0.5)` + log) que corra después de enviar la respuesta, sin bloquear el event loop. Además, el trabajo queda incompleto sin un README reproducible desde cero, un script de datos iniciales y los `.http` finales de los casos C-01 a C-08.

## What Changes

- Nueva corrutina `enviar_aviso_comprobante(venta_id, total)` con `await asyncio.sleep(0.5)` y `logger.info`.
- `POST /ventas/` inyecta `BackgroundTasks` y agenda el aviso después de crear la venta; la respuesta 201 no espera al aviso en producción.
- Tests: el aviso se registra en el log, el POST tarda al menos 0.5 s con el cliente ASGI, y una petición concurrente (`GET /health/live`) responde mientras el aviso duerme.
- Auditoría estática: sin `time.sleep`, `requests` ni drivers síncronos en `app/`.
- `scripts/seed.py` asincrónico e idempotente con datos de los casos C-01..C-08, sin `create_all` y leyendo `DATABASE_URL`.
- `README.md` final desde cero: requisitos, PostgreSQL, venv, dependencias, `.env`, `alembic upgrade head`, seed, uvicorn, endpoints, tests y estructura.
- `.http` finales: se documenta el aviso en `test/ventas.http` y se verifica la cobertura C-01..C-08.

## Impact

- Código: `app/modules/ventas/{service,router}.py`, `scripts/seed.py`, tests.
- Documentación: `README.md`, `test/ventas.http`, `CHANGES.md` al archivar.
- Sin cambios de esquema ni migraciones.
