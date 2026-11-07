# Librería: catálogo, clientes, ventas, acceso y despliegue — Base de Conocimiento

Base de conocimiento de dos consignas de Programación III (TUP) sobre una API FastAPI + PostgreSQL para una librería de barrio:

- **TP caps 1-4 "Del objeto a la persistencia" — implementado** (changes C-01..C-07, archivados). Fuente: `TP_Cap1a4_Consigna.pdf`.
- **Parcial caps 1-6 "Del objeto a la transacción" — pendiente** (changes C-08..C-16). Fuente: `docs/Parcial_Cap1a6_Consigna.txt` (`Parcial_Cap1a6_Consigna.pdf`). Agrega usuarios/roles/auth, repositorios + Unit of Work, stock por movimientos, borrado lógico y, aparte, el despliegue Docker en el VPS del TP caps 1-4.

Donde se superponen, el Parcial **reemplaza** al TP (cada archivo lo marca explícitamente como "TP (implementado)" o "Parcial (pendiente)"). Generada de las consignas, del Discovery (`discovery/discovery.md`) y de decisiones confirmadas.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos, alcance (7 ejercicios del TP + 10 del Parcial), fuera de alcance, entrega |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack (+ pydantic-settings, bcrypt, PyJWT, Docker), capas, integraciones, endpoints |
| [03_actores_y_roles.md](03_actores_y_roles.md) | ADMIN/VENDEDOR/CLIENTE, 401 vs 403, grupos de rutas, matriz endpoint/rol |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | 9 tablas del TP + 5 nuevas, índices únicos parciales, trigger, migraciones 0001-0004, seeds |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-01..RN-16 del Parcial, destino de las RN del TP, RNF |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas del TP (hechas) y del Parcial (por ejercicio y change) |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos del TP y del Parcial: registro, login, revocación, venta con stock, reposición, baja, Docker |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Capas Router→Service→UoW→Repository→Model, estructura obligatoria, seguridad, variables |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01…16 y SU-01…13 (con cuáles del TP quedan superadas) |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias (IN-01…10) y preguntas priorizadas |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md) y [09](09_decisiones_y_supuestos.md)

## Resumen Ejecutivo

**TP (hecho)**: API asincrónica de librería con PostgreSQL 16, SQLModel y Alembic; 7 ejercicios, 100 puntos.
**Parcial (pendiente)**: 10 ejercicios, 100 puntos (6, 10, 8, 14, 12, 16, 10, 6, 11, 7): config con pydantic-settings, acceso con bcrypt + JWT en cookie HttpOnly, roles vigentes en la base, repositorios + Unit of Work, `movimiento_stock` de solo agregado con trigger, borrado lógico con índice único parcial, `intento_acceso` en sesión propia, listados con envoltorio, y aparte la imagen Docker (python:3.12-alpine) y el despliegue en el VPS del TP caps 1-4 (`despliegue/`, DEPLOY.md, `evidencia/`).
**Roadmap**: C-08..C-16 (ver `09`, DD-07). Fuera de alcance: concurrencia (cap. 7), Redis (cap. 8), rol de base distinto para el solo-agregado.
**Nota**: `CHANGES.md`, `CLAUDE.md` y `AGENTS.md` aún describen solo el TP (ver IN-08 en `10`).
