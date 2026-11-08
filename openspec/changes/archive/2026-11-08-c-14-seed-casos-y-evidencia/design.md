# Design

## Context

El change C-14 es transversal y no modifica el esquema, los modelos ni los servicios de runtime. Consume lo ya implementado en C-08..C-13 (`Settings`, `UnitOfWork`, `BaseRepository`, `SoftDeleteRepository`, `MovimientoStock`, `borrado_en`, trigger de solo-agregado, autenticación, autorización, ventas atómicas).

Los artefactos que C-14 entrega ya existen en el filesystem (trabajo previo de C-13/C-14):
- `seed.py` en la raíz (idempotente, asincrónico, evento `SISTEMA`).
- `test/*.http` (C-01..C-13 + extras) con respuesta esperada comentada.
- `test/solo_agregado.sql` (caso C-14 de solo-agregado).
- `evidencia/C-14-seed.txt` y `evidencia/C-14-solo-agregado.txt` (capturas psql reales).
- `README.md` completo; `env.example` sin secretos.
- `tests/conftest.py`, `tests/ayuda.py`, `tests/test_c13_*.py`, `pytest.ini`.

Lo que puede faltar (no bloqueante): `evidencia/C-15-conteo-consultas.txt`.

## Goals / Non-Goals

**Goals:**
- Verificar que todos los entregables de C-14 están presentes y correctos.
- Completar cualquier entrega faltante de forma no disruptiva.
- Correr `python -m pytest -q` y reportar resultado.

**Non-Goals:**
- No modificar código de `app/`.
- No crear migraciones nuevas.
- No cambiar el esquema de base de datos.
- No crear tests unitarios ni de integración nuevos (el arnés ya existe en `tests/`).

## Decisions

| Decisión | Raciónale | Alternativa considerada |
|---|---|---|
| No escribir specs (skip_specs: true) | C-14 no cambia comportamiento observable de runtime; es documentación y evidencia. | Crear specs vacías (conflicta con `skip_specs`). |
| No reescribir `seed.py` ni otros archivos ya existentes | La regla de C-14 dice "NO reescribir código ya existente salvo lo estrictamente necesario". | Reescribir `seed.py` para "mejorarlo" (innecesario y arriesgado). |
| Crear `C-15-conteo-consultas.txt` solo si falta y es trivial | Es evidencia de apoyo no bloqueante; el README ya la menciona. | Ignorarla por completo (deja una referencia sin destino en el README). |

## Risks / Trade-offs

- [El seed no corre si faltan variables de entorno] → `tests/ayuda.py` ya define `JWT_SECRET_KEY`, `BCRYPT_COST`, `COOKIE_SECURE` para pytest; el seed usa `Settings()` que falla con mensaje claro si faltan `POSTGRES_PASSWORD` o `JWT_SECRET_KEY`.
- [pytest necesita base `libreria_test` y PostgreSQL local] → El conftest la recrea con `asyncpg` y `alembic upgrade head`; requiere PostgreSQL corriendo en :5432.

## Migration Plan

No aplica: no hay migraciones de esquema ni cambios de datos en producción. El cambio solo registra/verifica artefactos existentes.

## Open Questions

Ninguna.
