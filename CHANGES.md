# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto Parcial2-libreria (API de librería: FastAPI + SQLModel + PostgreSQL 16 + Alembic).
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas). Hay exactamente 7 changes, uno por ejercicio de la consigna (DD-01); ninguno se parte ni se fusiona.
> **Pruebas: todas son archivos `.http` en `test/`** (casos C-01 a C-08 más extras), con la respuesta esperada comentada. No hay tests unitarios, e2e ni pytest.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificá el próximo change con `[ ]` pendiente cuyas dependencias estén todas en `[x]`.
2. Leé los archivos de su sección **Leer antes** (KB) y la consigna `TP_Cap1a4_Consigna.pdf` para ese ejercicio.
3. Ejecutá `/opsx:propose <nombre-kebab-case>` y luego `/opsx:apply`.
4. Al terminar y verificar, ejecutá `/opsx:archive <nombre-kebab-case>`.
5. Marcá el checkbox de Estado: `[ ]` pendiente → `[x]` archivado.

---

## Árbol de dependencias

```
C-01 proyecto-conexion-ciclo-vida
 └── C-02 modelos-restricciones-relaciones
      └── C-03 migraciones-alembic
           └── C-04 contratos-crud
                └── C-05 altas-con-relaciones
                     ├── C-06 lecturas-sin-n-mas-uno
                     └── C-07 asincronia-sin-bloqueos
```

### Paralelismo por fase

```
GATE 0: (inicio)
  → C-01 proyecto-conexion-ciclo-vida          [Agente A]

GATE 1: C-01 ✓
  → C-02 modelos-restricciones-relaciones      [Agente A]  (único camino; C prepara seed.py / .http de apoyo sin tocar módulos)

GATE 2: C-02 ✓
  → C-03 migraciones-alembic                   [Agente A]

GATE 3: C-03 ✓
  → C-04 contratos-crud                        [Agente A]  (los módulos editoriales, generos, autores, libros, clientes pueden repartirse entre integrantes)

GATE 4: C-04 ✓
  → C-05 altas-con-relaciones                  [Agente A]

GATE 5: C-05 ✓                                  ← FORK
  → C-06 lecturas-sin-n-mas-uno                [Agente A]
  → C-07 asincronia-sin-bloqueos               [Agente B]
```

### Camino crítico (7 changes — mínimo irreducible)

C-01 → C-02 → C-03 → C-04 → C-05 → C-06* / C-07*

(* C-06 y C-07 son ambos "último" del camino: se ejecutan en paralelo.)

### Plan óptimo con 3 agentes

| Paso | Agente A (Backend Core) | Agente B (Backend Aux) | Agente C (Soporte/Docs) |
|------|-------------------------|------------------------|-------------------------|
| 1 | C-01 | — | README, env.example, requirements.txt |
| 2 | C-02 | — | scripts/seed.py (borrador) |
| 3 | C-03 | — | — |
| 4 | C-04 | — | test/*.http (CRUD) |
| 5 | C-05 | — | test/*.http (altas, casos C-01..C-08) |
| 6 | C-06 | C-07 | evidencia C-07 y .http finales |

---

## FASE 1 — Fundación

### [C-01] `proyecto-conexion-ciclo-vida`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 1; US-001, US-002):
  - Estructura: `app/main.py`, `app/core/config.py`, `app/core/database.py` y los 7 módulos (`health`, `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`) con `models.py/schemas.py/service.py/router.py`
  - `lifespan` en `main.py`: crea motor async (asyncpg) y fábrica de sesiones, los guarda en `app.state` y hace `dispose()` al apagar; `echo` configurable por `SQL_ECHO`
  - `get_session` con `Depends`: una sesión por petición, `expire_on_commit=False`
  - `GET /health/live` → `{"estado": "vivo"}` sin tocar la base; `GET /health/ready` → `SELECT 1`
  - `DATABASE_URL` leída de `.env`; `env.example` sin secretos; `requirements.txt` con versiones fijadas; `.gitignore` con `.env`
  - Prohibido `create_all` y credenciales en el repo
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios, §Variables de entorno
  - `knowledge-base/06_funcionalidades.md` §Épica 1
  - `knowledge-base/02_descripcion_general.md`
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03

---

## FASE 2 — Datos

### [C-02] `modelos-restricciones-relaciones`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 2; US-003):
  - Modelos de tabla: `Editorial`, `Genero`, `Autor`, `Libro`, `LibroAutor`, `Cliente`, `PerfilCliente`, `Venta`, `RenglonVenta` con los nombres de tablas/columnas exactos de la consigna
  - Constraints: UNIQUE (`editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email`, `perfil_cliente.cliente_id`); CHECK (`precio > 0`, `stock >= 0`, `orden >= 1`, `rol` en autor/coautor/traductor/ilustrador, `total >= 0`, `cantidad > 0`, `precio_unitario > 0`); PK compuesta de `libro_autor`
  - Índice por cada FK (`libro.editorial_id`, `libro.genero_id`, `libro_autor.autor_id`, `venta.cliente_id`, `renglon_venta.venta_id/libro_id`)
  - `Relationship(back_populates=...)` en ambos extremos; `Cliente.perfil` devuelve un objeto (uno a uno, `uselist=False`); `LibroAutor` como entidad propia, no `link_model`
  - Dinero con `Decimal` (NUMERIC(10,2) / (12,2)); `venta.fecha` con zona horaria
  - **Debe dejar `Genero` y `Libro.genero_id` (nullable, FK, índice) completamente definidos y aislables** para que C-03 los separe en la 2ª migración autogenerada
  - Pruebas (`.http`): constraints e índices verificados mediante los casos de rechazo (409/422) de `test/*.http` y la revisión de la migración
- **Dependencias**: `C-01`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (completo)
  - `knowledge-base/05_reglas_de_negocio.md` §Catálogo, §Clientes, §Ventas
  - `knowledge-base/06_funcionalidades.md` §Épica 2
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05, §DD-06

### [C-03] `migraciones-alembic`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 3; US-004):
  - Alembic con plantilla async (`alembic init -t async`); URL tomada del entorno, sin credenciales en `alembic.ini`; `env.py` apunta a `SQLModel.metadata` e importa todos los modelos
  - Migración 0001 (`--autogenerate`): las 9 tablas de la consigna menos `genero` (y sin `libro.genero_id`)
  - Migración 0002 (`--autogenerate` sobre la base ya migrada a 0001): agrega `genero` y `libro.genero_id` (nulo, con índice y FK nombrada); cabeza actual de la cadena
  - Revisión manual de cada migración con comentario explicativo; correcciones a mano si hace falta (CHECK, índices, tipos)
  - Verificar: `alembic upgrade head` sobre base vacía; `downgrade -1` + `upgrade head`
  - Script de datos iniciales `scripts/seed.py` (async) para los casos C-01..C-08: completado en C-07 (diferido desde C-03)
- **Dependencias**: `C-02`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica 3
  - `knowledge-base/07_flujos_principales.md` §Flujo 6
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04

---

## FASE 3 — API

### [C-04] `contratos-crud`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 4; US-005):
  - DTO `Create/Update/Read` separados de los modelos de tabla (altas sin `id`) en editoriales, géneros, autores, libros y clientes
  - Endpoints: `POST`, `GET` (lista), `GET {id}`, `PATCH {id}` por recurso; PATCH con `exclude_unset`; sin PATCH de ventas
  - Códigos: 201 al crear, 404 inexistente, 409 ante `IntegrityError` (ISBN/email/nombre duplicado, CHECK) con mensaje propio, 422 contrato
  - Handler global que traduce `IntegrityError` a 409 sin texto interno de la base (RN-12)
  - Endpoints de relación: `GET /editoriales/{id}/libros`, `GET /generos/{id}/libros`, `GET /autores/{id}/libros` (con rol y orden) y `GET /clientes/{id}/ventas` (404 si el padre no existe)
  - Paginación `limit` 1-100 (def. 20) y `offset >= 0`, respuesta = lista simple; `GET /libros/?titulo=` con `icontains` (parámetro ligado) (caso C-08: inyección → 200 lista vacía); filtro `genero_id`
  - Archivos `test/*.http` con respuesta esperada comentada
- **Dependencias**: `C-03`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica 4
  - `knowledge-base/05_reglas_de_negocio.md` §Listados y errores, §Excepciones globales
  - `knowledge-base/07_flujos_principales.md` §Flujo 5
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad

### [C-05] `altas-con-relaciones`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 5; US-006, US-007, US-008):
  - `POST /libros/` con `editorial_id`, `genero_id`, `autores[{autor_id, rol, orden}]`: crea `Libro` + `LibroAutor` en una transacción, sin `if` de existencia previa; FK/ISBN/CHECK rechazado → 409 con mensaje propio
  - `POST /clientes/{id}/perfil`: segundo perfil → 409 por UNIQUE (RN-09)
  - `POST /ventas/` con `cliente_id` y `renglones[{libro_id, cantidad}]`: validación 422 (al menos un renglón, sin `libro_id` repetido, `cantidad > 0`); lee precios del libro, copia `precio_unitario`, total `Σ cantidad × precio` con `Decimal` calculado por el servidor, `fecha` del servidor; cliente/libro inexistente → 409; respuesta 201 con cliente y renglones (`titulo`, `precio_unitario`, `subtotal`)
  - Sin PATCH de ventas; el stock no se descuenta (SU-01)
  - Pruebas `.http`: altas correctas, ISBN repetido, perfil duplicado, venta con libro repetido e inexistente
- **Dependencias**: `C-04`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 1, §Flujo 2, §Flujo 4
  - `knowledge-base/05_reglas_de_negocio.md` §Ventas (RN-04..RN-08)
  - `knowledge-base/06_funcionalidades.md` §Épica 5
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05, §SU-02, §SU-03
  - `knowledge-base/10_preguntas_abiertas.md` §IN-01

---

## FASE 4 — Calidad y asincronía

> C-06 y C-07 son independientes entre sí y pueden ejecutarse en paralelo tras C-05 (tocan archivos distintos: servicios de lectura vs. router de ventas/background).

### [C-06] `lecturas-sin-n-mas-uno`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 6; US-009):
  - `GET /libros/{id}`: una consulta con `joinedload` (editorial, género) y `selectinload` (autorías → autor)
  - `GET /ventas/{id}` y respuesta del alta: `joinedload` (cliente) y `selectinload` (renglones → libro)
  - Listados de libros con el detalle precargado; ninguna lectura depende de carga perezosa
  - Cantidad de consultas fija con 1 o N autores/renglones; evidencia C-07 con `SQL_ECHO=true` en consola
  - Pruebas `.http` (`test/C-07-detalles.http`): mismo conteo de sentencias SQL en consola con 1 vs. varios autores/renglones
- **Dependencias**: `C-05`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 3
  - `knowledge-base/06_funcionalidades.md` §Épica 6
  - `knowledge-base/05_reglas_de_negocio.md` §Requisitos no funcionales (NF-04, RN-12)
  - `knowledge-base/04_modelo_de_datos.md` §Navegación

### [C-07] `asincronia-sin-bloqueos`
- **Estado**: `[x]` archivado
- **Scope** (Ejercicio 7; US-010):
  - Aviso de comprobante con `BackgroundTasks` agendado en `POST /ventas/`: `await asyncio.sleep(0.5)` + log; corre después de enviar la respuesta
  - Auditoría de handlers/servicios: todo `async def`, sin `time.sleep`, `requests` ni drivers síncronos
  - Verificar que el servidor atiende otras peticiones durante el aviso (dos requests concurrentes)
  - README final desde cero (venv, dependencias, `.env`, `alembic upgrade head`, seed, uvicorn) y `.http` finales de los casos C-01..C-08
- **Dependencias**: `C-05`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica 7, §Entregables transversales
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 (paso 7)
  - `knowledge-base/08_arquitectura_propuesta.md` §Entorno de desarrollo
  - `knowledge-base/01_vision_y_objetivos.md`

---

## Resumen

| ID | Change | Ejercicio (pts) | Depende de | Governance | Estado |
|----|--------|-----------------|------------|------------|--------|
| C-01 | proyecto-conexion-ciclo-vida | 1 (10) | — | BAJO | `[x]` |
| C-02 | modelos-restricciones-relaciones | 2 (25) | C-01 | CRITICO | `[x]` |
| C-03 | migraciones-alembic | 3 (10) | C-02 | ALTO | `[x]` |
| C-04 | contratos-crud | 4 (15) | C-03 | MEDIO | `[x]` |
| C-05 | altas-con-relaciones | 5 (20) | C-04 | ALTO | `[x]` |
| C-06 | lecturas-sin-n-mas-uno | 6 (10) | C-05 | MEDIO | `[x]` |
| C-07 | asincronia-sin-bloqueos | 7 (10) | C-05 | MEDIO | `[x]` |
