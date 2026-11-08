# Proposal

## Why

El parcial necesita un punto único y verificable de datos iniciales (`seed.py`) que deje la base en un estado conocido para los casos `.http` y las pruebas automáticas, más capturas de evidencia reales (`evidencia/`) que demuestren que el seed, el trigger de solo-agregado y las consultas del detalle de venta funcionan según la consigna. Sin este cambio no hay forma de reproducir el estado inicial ni de evidenciar el cumplimiento de los requisitos transversales (US-122).

## What Changes

- `seed.py` en la raíz: idempotente, asincrónico, vacía tablas con `TRUNCATE ... RESTART IDENTITY CASCADE`, carga 5 usuarios, 3 editoriales, 3 géneros, 6 autores, 5 libros con stock = suma de movimientos, 3 clientes, la venta 1 de Lucía (69000.00) y un evento `SISTEMA` en `evento_seguridad`. Ya existe; se verifica y documenta.
- `test/*.http`: casos C-01..C-13 del parcial con respuesta esperada comentada, ya existentes; se verifican contra la implementación actual.
- `test/solo_agregado.sql`: caso C-14 que comprueba que `movimiento_stock` rechaza `UPDATE` y `DELETE` (migración 0004). Ya existe; se verifica.
- `evidencia/C-14-seed.txt` y `evidencia/C-14-solo-agregado.txt`: capturas psql reales ya existentes; se verifican.
- `evidencia/C-15-conteo-consultas.txt` (opcional, no bloqueante): consultas del detalle de venta con 2 y 4 renglones e igual conteo, si falta se considera crearla como evidencia de apoyo.
- `README.md`: ya completo con pasos desde cero, usuarios de seed, casos `.http`, evidencia, estructura y pruebas pytest; se verifica.
- `env.example`: ya existe sin secretos; se verifica.
- No se modifica código de runtime ni esquema de base de datos; no hay cambios de comportamiento.

## Capabilities

### New Capabilities

Ninguna: este change no introduce comportamiento nuevo de runtime.

### Modified Capabilities

Ninguna: no cambian requisitos de ninguna capacidad existente (`openspec/specs/`).

## Impact

- Afecta solo artefactos de documentación y evidencia: `seed.py`, `test/*.http`, `test/solo_agregado.sql`, `evidencia/`, `README.md`, `env.example`.
- No toca `app/`, `migrations/`, ni `alembic.ini`.
- No hay rutas nuevas, ni cambios de esquema, ni rotación de secretos.
- Conexión con C-13: consume los modelos, migraciones, repositorios, UoW y servicios que C-13 ya implementó (stock por movimientos, baja lógica, ventas atómicas); `seed.py` usa `registrar_movimiento` y `UnitOfWork` de C-09/C-13.
