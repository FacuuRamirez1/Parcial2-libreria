# Tasks

## 1. Verificación de entregables existentes

- [ ] 1.1 Verificar que `seed.py` existe en la raíz y es idempotente/asincrónico con evento `SISTEMA`. Verificación: `python seed.py` corre sin errores y reporta invariante `stock == suma(movimientos)` OK.
- [ ] 1.2 Verificar que `test/*.http` existen para C-01..C-13 con respuesta esperada comentada. Verificación: `Get-ChildItem test\ -Filter *.http` lista 15 archivos.
- [ ] 1.3 Verificar que `test/solo_agregado.sql` existe y prueba UPDATE/DELETE rechazados en `movimiento_stock`. Verificación: el archivo existe y contiene los bloques UPDATE y DELETE con comentarios de ERROR esperados.
- [ ] 1.4 Verificar que `evidencia/C-14-seed.txt` y `evidencia/C-14-solo-agregado.txt` existen con capturas psql reales. Verificación: ambos archivos existen y contienen salidas de `SELECT`.
- [ ] 1.5 Verificar que `README.md` está completo (pasos desde cero, usuarios de seed, casos .http, evidencia, estructura, pytest). Verificación: el archivo existe y tiene las secciones 1-12.
- [ ] 1.6 Verificar que `env.example` existe sin secretos. Verificación: el archivo existe y no contiene valores reales de `POSTGRES_PASSWORD` ni `JWT_SECRET_KEY`.

## 2. Completar entregable faltante (no bloqueante)

- [ ] 2.1 Verificar si existe `evidencia/C-15-conteo-consultas.txt`. Si no existe, crearla como evidencia de apoyo con las consultas del detalle de venta (2 y 4 renglones, igual conteo). Verificación: el archivo existe o se decide conscientemente no crearla.

## 3. Validación con pytest

- [ ] 3.1 Ejecutar `python -m pytest -q` y reportar cuántos tests pasan / fallan. Verificación: el comando termina y se reporta el resultado (pass/fail y conteo).

## Workflow follow-up

- Ejecutar `openspec instructions archive --change "c-14-seed-casos-y-evidencia" --json` y luego `openspec archive change "c-14-seed-casos-y-evidencia"` para sincronizar delta specs y cerrar el change.
- Guardar observación `mem_save` con topic_key `opsx/c-14-seed-casos-y-evidencia/archive`.
