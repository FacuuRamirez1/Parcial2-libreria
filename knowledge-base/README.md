# Librería: catálogo, clientes y ventas — Base de Conocimiento

Base de conocimiento del TP "Del objeto a la persistencia" (Programación III, TUP): una API FastAPI + PostgreSQL para una librería de barrio. Se generó a partir de la consigna (`TP_Cap1a4_Consigna.pdf`), del Discovery (`discovery/discovery.md`) y de una ronda de confirmación con el usuario.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos, alcance (7 ejercicios), fuera de alcance |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack, arquitectura, integraciones, endpoints |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores (sin RBAC: auth fuera de alcance) |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | 9 tablas, restricciones, relaciones y seed |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-01 a RN-12 y requisitos no funcionales |
| [06_funcionalidades.md](06_funcionalidades.md) | 7 épicas (una por ejercicio) con historias y criterios |
| [07_flujos_principales.md](07_flujos_principales.md) | Venta, alta de libro, detalle sin N+1, perfil, búsqueda, esquema |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, estructura de directorios, seguridad, variables de entorno |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01…06 y SU-01…06 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Inconsistencias y preguntas priorizadas |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

API asincrónica de librería (editoriales, géneros, autores, libros, clientes y ventas) con PostgreSQL 16, SQLModel y migraciones Alembic. Se evalúa por 7 ejercicios (100 puntos) y cada uno es un change del roadmap. Las claves de calidad son: restricciones en la base, carga anticipada sin N+1, traducción de `IntegrityError` a 409 y asincronía sin bloqueos. La lista de endpoints se verificó contra el PDF y las ventas con ids inexistentes responden 409.
