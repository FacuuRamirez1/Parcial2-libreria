# Parcial2-libreria — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

| Capa | Tecnología | Versión mínima |
|------|------------|----------------|
| Lenguaje | Python | 3.12 |
| Framework web | FastAPI (todos los handlers `async def`) | 0.111 |
| Modelos y contratos | SQLModel | 0.0.24 |
| ORM / motor / sesión | SQLAlchemy asincrónico | 2.0 |
| Driver | asyncpg | 0.30 |
| Base de datos | PostgreSQL | 16 |
| Migraciones | Alembic (plantilla asincrónica) | 1.13 |
| Configuración | python-dotenv | 1.0 |
| Servidor ASGI | uvicorn (el de `fastapi[standard]`) | — |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.** La consigna original es `TP_Cap1a4_Consigna.pdf`.

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance (los 7 ejercicios) |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Actores (sin auth ni RBAC) |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Tablas, restricciones, relaciones, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | RN-01 a RN-12 y requisitos no funcionales NF-01 a NF-07 |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias por épica (una épica = un ejercicio = un change) |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Venta, alta de libro, detalle sin N+1, perfil, búsqueda |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura de directorios, variables de entorno |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | DD-01…06 y SU-01…06 |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |

> ✅ Las preguntas de prioridad **Alta** están resueltas: el listado de endpoints se verificó contra el PDF y una venta con libro o cliente inexistente responde 409. Quedan abiertas solo preguntas Media/Baja (ver `10_preguntas_abiertas.md`).

---

## Skills Disponibles

Instaladas a nivel proyecto en `.claude/skills/`.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI, módulos router/service/schemas, lifespan, async | `fastapi`, `fastapi-templates`, `python-backend` |
| **Datos y Migraciones** | Modelos SQLModel, restricciones, Alembic, carga anticipada | `sqlmodel`, `postgresql-table-design`, `database-patterns`, `python-backend` |
| **Orquestación** | OPSX / documentación / roadmap | `kb-creator`, `roadmap-generator`, `agent-instruction`, `skill-creator` |

Cargá la skill correspondiente al contexto ANTES de escribir código.

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.
> `fastapi-templates` sugiere repositorios/Unit of Work: este proyecto **no** los usa (capítulo 6 fuera de alcance).

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 7 changes, uno por ejercicio de la consigna (sin extras, partidos ni fusionados).
- **Camino crítico** (7): `C-01 → C-02 → C-03 → C-04 → C-05 → C-06 / C-07` (C-06 y C-07 corren en paralelo tras C-05).
- **Primer change**: `C-01` (`proyecto-conexion-ciclo-vida`).

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras

> Reglas **globales** ya definidas en `~/.claude/CLAUDE.md` (orquestador, governance, TDD, engram): el proyecto las **hereda**, no se repiten acá. Acá viven solo las reglas **específicas de este proyecto** + las universales que el global no cubre.

### Datos y base
- NUNCA `create_all` → el esquema se crea únicamente con Alembic (`alembic upgrade head`).
- NUNCA `float` para dinero → `Decimal` en Python y `NUMERIC(10,2)` / `NUMERIC(12,2)` en la base.
- NUNCA pre-consultar unicidad o existencia de ids → escribir y dejar que UNIQUE / FK rechacen; responder 409.
- NUNCA devolver texto interno de la base (tablas, restricciones, trazas) → traducir `IntegrityError` a un mensaje propio.

### Lecturas y async
- NUNCA carga perezosa → `joinedload` (relaciones a uno) y `selectinload` (colecciones) declarados en la misma consulta.
- NUNCA llamadas bloqueantes en handlers (`time.sleep`, `requests`, acceso síncrono a la base) → todo `async def`.
- NUNCA SQL armado por concatenación con datos del usuario → parámetros ligados.

### Proyecto
- NUNCA credenciales en el código, en `alembic.ini` ni en el repo → `DATABASE_URL` en `.env` (no versionado) y `env.example` sin secretos.
- NUNCA renombrar ni quitar tablas o columnas de la consigna → solo se pueden agregar columnas.
- NUNCA crear changes fuera de los 7 de `CHANGES.md` → un change por ejercicio, sin extras.

### Universales (no cubiertas por el global)
- NUNCA buildear ni commitear sin que el usuario lo pida → esperar la orden explícita.
- Commits convencionales (`feat:`, `fix:`, `chore:`, `docs:`…).

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
