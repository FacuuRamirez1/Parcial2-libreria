# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto Parcial2-libreria (API de librería: FastAPI + SQLModel + PostgreSQL 16 + Alembic).
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas). Hay **16 changes**: C-01..C-07 (TP caps 1-4, un change por ejercicio, DD-01) están **archivados e intactos**; C-08..C-16 (Parcial caps 1-6, DD-07) son uno por bloque de la consigna `docs/Parcial_Cap1a6_Consigna.txt`. Ninguno extra, partido ni fusionado fuera de esta lista.
> **Pruebas: todas son archivos `.http` en `test/`** con la respuesta esperada comentada (casos C-01..C-16 del parcial, D-01..D-08 del despliegue), más `test/solo_agregado.sql`. No hay tests unitarios, e2e ni pytest salvo lo que ya exista en el repo.
> **Cada change del Parcial "conecta" con lo existente**: modifica lo mínimo de C-01..C-07 (se indica por change) y no rehace lo ya implementado (DD-08). Lo que el Parcial reemplaza está en DD-09.
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificá el próximo change con `[ ]` pendiente cuyas dependencias estén todas en `[x]`.
2. Leé los archivos de su sección **Leer antes** (KB) y la consigna (`TP_Cap1a4_Consigna.pdf` para C-01..C-07; `docs/Parcial_Cap1a6_Consigna.txt` para C-08..C-16). Los códigos/roles marcados `(*)` en la KB son inferidos: confirmarlos contra la consigna en cada propose.
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
                     ├── C-06 lecturas-sin-n-mas-uno      [x]
                     └── C-07 asincronia-sin-bloqueos     [x]
                          └── C-08 settings-y-base-de-capas
                               ├── C-09 modulos-a-repositorios-uow ──────────┐
                               └── C-10 modelos-acceso-stock-migraciones ────┤  (C-09 y C-10 en paralelo)
                                                                              └── C-11 autenticacion
                                                                                   └── C-12 autorizacion-roles-y-rutas
                                                                                        └── C-13 stock-movimientos-baja-logica-ventas  (también requiere C-10)
                                                                                             └── C-14 seed-casos-y-evidencia

C-15 imagen-docker-tp-cap1a4   (sin dependencias: solo usa el snapshot git f1b9b48; puede correr desde ya)
 └── C-16 despliegue-vps       (requiere acceso al VPS)
```

### Paralelismo por fase

```
GATE 0..5: C-01..C-07 ✓ (archivados; ver historial)

GATE 6: (inicio del Parcial; C-07 ✓)             ← FORK
  → C-08 settings-y-base-de-capas              [Agente A]
  → C-15 imagen-docker-tp-cap1a4               [Agente C]  (independiente del código del parcial; PRIMER paso: tag git sobre f1b9b48)

GATE 7: C-08 ✓                                  ← FORK
  → C-09 modulos-a-repositorios-uow            [Agente A]
  → C-10 modelos-acceso-stock-migraciones      [Agente B]  (archivos distintos: módulos existentes vs. modelos/migraciones nuevos; coordinar import de modelos en alembic/env.py)

GATE 8: C-09 ✓ y C-10 ✓
  → C-11 autenticacion                         [Agente A]
  → C-16 despliegue-vps                        [Agente C — si C-15 ✓; acciones manuales en VPS]

GATE 9: C-11 ✓
  → C-12 autorizacion-roles-y-rutas            [Agente A]

GATE 10: C-12 ✓ (y C-10 ✓)
  → C-13 stock-movimientos-baja-logica-ventas  [Agente A]

GATE 11: C-13 ✓
  → C-14 seed-casos-y-evidencia                [Agente A]  (README y .http de apoyo pueden adelantarse con Agente C)
```

### Camino crítico (14 changes — mínimo irreducible)

C-01 → C-02 → C-03 → C-04 → C-05 → C-07 → C-08 → C-09* / C-10* → C-11 → C-12 → C-13 → C-14

(C-01..C-07 ya archivados; el tramo pendiente es C-08 → C-09* / C-10* → C-11 → C-12 → C-13 → C-14. C-09 y C-10 corren en paralelo y ambos deben estar listos antes de C-11. La rama C-15 → C-16 es independiente del código y no integra el camino crítico, pero es obligatoria para la entrega.)

### Plan óptimo con 3 agentes (Parcial)

| Paso | Agente A (Backend Core) | Agente B (Datos/Migraciones) | Agente C (Soporte/Despliegue) |
|------|-------------------------|------------------------------|-------------------------------|
| 1 | C-08 | — | C-15 (tag f1b9b48, Dockerfile en `despliegue/`) |
| 2 | C-09 | C-10 | C-15 (cierre) / borrador `.http` |
| 3 | C-11 | — | C-16 (VPS, acciones manuales del usuario) |
| 4 | C-12 | — | C-16 / `.http` de auth y roles |
| 5 | C-13 | — | README del parcial, `env.example` |
| 6 | C-14 | — | evidencia D-01..D-08 y zip final |

(Plan histórico de C-01..C-07: ver el historial de git; todos archivados.)

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

## FASE 5 — Base de capas del Parcial

### [C-08] `settings-y-base-de-capas`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 1 del Parcial, 6 pts; US-101..US-103):
  - `app/core/config.py`: `Settings` con `pydantic-settings` (`POSTGRES_*`, clave de firma JWT y contraseña **sin valor por defecto**, costo de bcrypt, tamaño de pool, flag `Secure` de la cookie); reemplaza `python-dotenv`/`DATABASE_URL` en el parcial (DD-09, IN-07)
  - `app/core/repository.py`: `BaseRepository[T]` y `SoftDeleteRepository[T]` (genéricos; la lógica específica llega en C-09)
  - `app/core/unit_of_work.py`: `UnitOfWork` base (sesión, `commit`/`rollback`, `async with`)
  - `app/core/paginacion.py`: envoltorio `{items,total,page,size,pages}` (solo el contenedor genérico; su uso en listados es C-09)
  - `lifespan`: hash ficticio de bcrypt calculado al arrancar (insumo de RN-08); motor y fábrica con pool configurable
  - `GET /health/ready` responde 503 si la base no contesta (IN-09); `get_session` ajustado
  - Pruebas `.http`: arranque sin variables obligatorias falla; ready 200/503
- **Conecta con**: modifica mínimamente `app/core/config.py`, `app/core/database.py`, `app/main.py`, `app/health/router.py`, `requirements.txt` y `env.example` (C-01); no toca módulos de dominio.
- **Dependencias**: `C-07`
- **Governance**: ALTO (configuración y secretos)
- **Leer antes**:
  - `knowledge-base/08_arquitectura_propuesta.md` §Capas, §Patrones aplicados, §Variables de entorno
  - `knowledge-base/06_funcionalidades.md` §Épica P1
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-08, §DD-09, §SU-07
  - `knowledge-base/10_preguntas_abiertas.md` §IN-06, §IN-07, §IN-09

---

## FASE 6 — Refactor a capas y modelo de acceso

> C-09 y C-10 son independientes y pueden ejecutarse en paralelo tras C-08. Ojo con conflictos en `alembic/env.py` y `app/main.py` (import de modelos y routers).

### [C-09] `modulos-a-repositorios-uow`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 6 parcial parte 1, repositorios y UoW, 16 pts; Ejercicio 3 parcial, contratos, 8 pts; parte N+1 del Ejercicio 8; US-106, US-113, US-114, US-117):
  - Migrar `editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas` a `models/schemas/repository/unit_of_work/service/router`
  - Servicios reciben el `UnitOfWork` (no la sesión); `commit`/`rollback` en el UoW; un repositorio por entidad sobre `BaseRepository`/`SoftDeleteRepository`
  - La precarga (`joinedload`/`selectinload`) se declara en el repositorio y conserva el resultado de C-06 (conteo fijo de consultas)
  - Listados con `{items,total,page,size,pages}` (`page` ≥ 1, `size` 1-100 def. 20; página inexistente → 422; `total` con los mismos filtros; cero resultados = página vacía); reemplaza `limit/offset` (DD-09)
  - DTO de entrada con `extra="forbid"`; PATCH con `exclude_unset`; sin `password_hash` en respuestas
  - Conserva el comportamiento observable del TP (201/404/409/422, mensajes propios, rutas de relación) salvo lo que el Parcial reemplaza; las rutas del TP que la tabla no lista se conservan (IN-04, SU-11)
  - Pruebas `.http`: repetir los casos de `test/*.http` del TP contra el refactor (regresión) + paginación nueva
- **Conecta con**: modifica `service.py`, `router.py` y `schemas.py` de los 6 módulos de C-04/C-05/C-06 y agrega `repository.py`/`unit_of_work.py` por módulo; los modelos de C-02 no cambian de esquema.
- **Dependencias**: `C-08`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica P3, §Épica P6, §Épica P8
  - `knowledge-base/08_arquitectura_propuesta.md` §Capas, §Patrones aplicados, §Estructura de directorios
  - `knowledge-base/05_reglas_de_negocio.md` §Reglas adicionales (listados, contratos)
  - `knowledge-base/07_flujos_principales.md` §Flujo 3, §Flujo P10
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-08, §DD-09, §SU-11

### [C-10] `modelos-acceso-stock-migraciones`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 2 parcial, 10 pts; trigger del Ejercicio 7 parcial, 10 pts; US-104, US-105, US-115; RN-01, RN-03, RN-12):
  - Modelos: `Usuario`, `AsignacionRol`, `IntentoAcceso`, `EventoSeguridad`, `MovimientoStock` con CHECK/UNIQUE e índice por FK; índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`
  - Cambios: `cliente.usuario_id` (UNIQUE, nulo, FK) y `libro.borrado_en` + índice único parcial del ISBN (reemplaza `UNIQUE(isbn)`, DD-09); solo se agregan columnas
  - Migración 0003 con `--autogenerate`, leída y comentada a mano (índices parciales y reemplazo del UNIQUE del ISBN revisados)
  - Migración 0004 escrita a mano: trigger de solo-agregado sobre `movimiento_stock` (UPDATE/DELETE rechazados), con `downgrade` que lo elimina
  - Verificar `upgrade head` en base vacía y `downgrade -1` + `upgrade head`; stock existente vs. invariante (IN-05, SU-13)
  - Pruebas: borrador de `test/solo_agregado.sql` y `.http` de rechazos de constraints
- **Conecta con**: modifica `app/libros/models.py` y `app/clientes/models.py` (C-02) y `alembic/env.py` (importar modelos nuevos); suma 0003 y 0004 a `alembic/versions/` (C-03: 0001 y 0002 intactas).
- **Dependencias**: `C-08`
- **Governance**: CRITICO (migraciones, trigger, tablas de seguridad)
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` (completo)
  - `knowledge-base/06_funcionalidades.md` §Épica P2, §Épica P7
  - `knowledge-base/05_reglas_de_negocio.md` §Parcial RN-01, RN-03, RN-12
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-09, §SU-13
  - `knowledge-base/10_preguntas_abiertas.md` §IN-05

---

## FASE 7 — Autenticación y autorización

### [C-11] `autenticacion`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 4 parcial, 14 pts; parte `intento_acceso` del Ejercicio 7; US-107..US-109, US-116; RN-02, RN-07, RN-08, RN-15):
  - Módulo `usuarios` (`models/schemas/repository/unit_of_work/service/router`) y bcrypt en `app/core/`
  - bcrypt siempre fuera del bucle de eventos (`asyncio.to_thread`) y bajo un semáforo; costo de `Settings`; hash calculado antes de abrir la transacción; límite de 72 **bytes** → 422 en registro, login y cambio
  - JWT (HS256, SU-08) en cookie `HttpOnly`, `SameSite=Lax`, `Max-Age`, `Secure` configurable; sin cabecera `Authorization` (DD-11)
  - `POST /auth/registro`: usuario + rol CLIENTE + cliente en un solo UoW (RN-02); correo de cliente existente → 409 sin apropiarse de la ficha; no inicia sesión (SU-10)
  - `POST /auth/login`: orden 429 (`Retry-After`, sin hash) → verificación (contra hash ficticio si el correo no existe, RN-08) → cookie
  - `intento_acceso` en sesión y transacción propias, siempre confirmada, con el comentario de 3 cosas (qué hace distinto, por qué no comparte transacción, costo); login correcto reinicia la cuenta (RN-07)
  - `POST /auth/logout`, `GET /auth/yo`, `POST /auth/cambiar-password` (deja `debe_cambiar_password` en falso, sin token nuevo)
  - Pruebas `.http`: registro, correo duplicado, login correcto/incorrecto/inexistente, 5 fallos → 429, password > 72 bytes
- **Conecta con**: modifica `app/main.py` (montar router `/auth`) y `app/clientes/` (alta de cliente con `usuario_id` dentro del UoW de registro); usa modelos de C-10 y UoW/repositorios de C-09.
- **Dependencias**: `C-09`, `C-10`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Modelo de roles, §Códigos de seguridad
  - `knowledge-base/05_reglas_de_negocio.md` §Parcial RN-02, RN-07, RN-08, RN-15; §Reglas adicionales
  - `knowledge-base/06_funcionalidades.md` §Épica P4, §US-116
  - `knowledge-base/07_flujos_principales.md` §Flujo P1, §Flujo P2
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-11, §DD-14, §SU-08, §SU-09, §SU-10

### [C-12] `autorizacion-roles-y-rutas`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 5 parcial, 12 pts; US-110..US-112; RN-03, RN-04, RN-05, RN-06, RN-14, RN-16):
  - `get_usuario_actual` (cookie ausente/inválida → 401) y `requiere_rol(...)` (403): roles **vigentes leídos de la base en cada petición**, en la misma sesión que luego usa el UoW (RN-04, DD-10); roles del token solo informativos
  - Dos grupos de rutas en `app/main.py`: sin sesión (health, registro, login) y con sesión; el control de cambio obligatorio de contraseña (RN-06, 403) montado **una sola vez** sobre el grupo protegido, con excepción de `/auth/*`
  - Alta de personal (usuario con rol de personal y `debe_cambiar_password`); asignar/revocar roles con vigencia: vencimiento sin zona o pasado → 422, duplicado abierto → 409 (RN-03), reasignar un rol vencido cierra la fila y abre otra; autoprotección (no revocarse ADMIN ni quedar sin administradores, RN-05, 409)
  - `evento_seguridad` en la misma transacción del cambio (RN-16); `GET /eventos` (ADMIN)
  - Protección de las rutas existentes según la matriz de roles; las rutas de lo propio solo piden autenticación (RN-14); el detalle de venta sin `requiere_rol` (decisión en el servicio, C-13)
  - Pruebas `.http` con varias sesiones (`# @name`, `@no-cookie-jar`): 401/403, revocación con sesión abierta (Flujo P4), cambio obligatorio (Flujo P9)
- **Conecta con**: modifica `app/main.py` y los `router.py` de editoriales, generos, autores, libros, clientes y ventas (agregar `Depends`/grupos); no cambia servicios de dominio.
- **Dependencias**: `C-11`
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` (completo: §Grupos de rutas, §Matriz de endpoints y roles)
  - `knowledge-base/05_reglas_de_negocio.md` §Parcial RN-03..RN-06, RN-14, RN-16
  - `knowledge-base/06_funcionalidades.md` §Épica P5
  - `knowledge-base/07_flujos_principales.md` §Flujo P3, §Flujo P4, §Flujo P9
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-10, §SU-12

---

## FASE 8 — Stock, bajas y ventas

### [C-13] `stock-movimientos-baja-logica-ventas`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 6 parcial parte 2 y Ejercicio 8 parcial, 6 pts; US-117..US-121; RN-09, RN-10, RN-11, RN-13, RN-14):
  - Único punto de escritura de stock; `PATCH /libros/{id}` con `stock` → 422 (`extra="forbid"`)
  - `POST /libros` con `stock_inicial` (movimiento de alta); `POST /libros/{id}/reponer`; `GET /libros/{id}/movimientos`
  - `DELETE /libros/{id}` baja lógica → 204; sale del catálogo; re-alta del mismo ISBN → 201, segundo vigente → 409; vender o reponer un libro dado de baja → 409
  - `POST /ventas`: descuenta stock + un movimiento por renglón + venta y renglones en un solo UoW; stock insuficiente, libro/cliente inexistente o dado de baja → 409 sin escrituras parciales (RN-10)
  - `BackgroundTasks` solo tras confirmar (agendado después del `commit`), con logger visible con uvicorn normal
  - Detalle de venta con número fijo de consultas incluso si el libro fue dado de baja
  - `GET /mis-ventas` (solo autenticado), `GET /ventas/{id}` con decisión de dueño en el servicio (403, RN-14), `GET /ventas` solo ADMIN
  - Invariante `stock = Σ cantidad de movimientos`
  - Pruebas `.http`: venta exitosa, stock insuficiente atómico, baja y re-alta, dueño vs. ajeno
- **Conecta con**: modifica `app/libros/{service,repository,router,schemas}.py` y `app/ventas/{service,repository,router}.py` (C-05/C-06/C-07; reemplaza SU-01 y el aviso actual); usa `MovimientoStock` y `borrado_en` de C-10 y la autorización de C-12.
- **Dependencias**: `C-12`, `C-10`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §Parcial RN-09..RN-14; §Reglas adicionales
  - `knowledge-base/06_funcionalidades.md` §Épica P8, §Épica P9
  - `knowledge-base/07_flujos_principales.md` §Flujo P5, §Flujo P6, §Flujo P7, §Flujo P8
  - `knowledge-base/04_modelo_de_datos.md` §libro, §movimiento_stock, §Navegación
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-09, §SU-12

---

## FASE 9 — Evidencia y entrega

### [C-14] `seed-casos-y-evidencia`
- **Estado**: `[ ]` pendiente
- **Scope** (transversal a los ejercicios del Parcial; US-122; entregables transversales):
  - `seed.py` en la **raíz** según la tabla de datos iniciales, con evento `SISTEMA` en `evento_seguridad`; se mueve `scripts/seed.py` a la raíz (IN-02b, DD-12); asincrónico e idempotente
  - `test/*.http` casos C-01..C-16 del parcial con varias sesiones (`# @name`, `@no-cookie-jar`) y respuesta esperada comentada
  - `test/solo_agregado.sql` (caso C-14: UPDATE/DELETE sobre `movimiento_stock` rechazados) y `evidencia/` (captura psql de C-14; consultas del caso C-15 con 2 y 4 renglones e igual conteo)
  - README del parcial: integrantes, pasos desde cero (venv, dependencias, `.env`, `alembic upgrade head`, `python seed.py`, uvicorn), cómo generar la clave de firma; `env.example` sin secretos
  - Verificar el entregable: `parcial/` sin `.venv`, `__pycache__` ni `.env`
- **Conecta con**: mueve `scripts/seed.py` (C-03/C-07; el snapshot de C-15 conserva el original), reemplaza `README.md` y `env.example` de C-01/C-07 y amplía los `test/*.http` de C-04..C-07.
- **Dependencias**: `C-13`
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Seed data inicial
  - `knowledge-base/06_funcionalidades.md` §Épica P10, §Entregables transversales (Parcial)
  - `knowledge-base/07_flujos_principales.md` §Flujo P11
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-12
  - `knowledge-base/10_preguntas_abiertas.md` §IN-02b

---

## FASE 10 — Contenedor y despliegue del TP

> Independiente del código del Parcial: usa solo el snapshot del TP caps 1-4. C-15 puede ejecutarse desde ya, en paralelo con C-08..C-14.

### [C-15] `imagen-docker-tp-cap1a4`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 9 parcial, 11 pts; US-123; Flujo P12):
  - **Primer paso**: tag de git sobre `f1b9b48` (snapshot del TP caps 1-4) y copia de ese estado a `despliegue/` (sin `.venv`, `__pycache__`, `.env`)
  - Agregar solo `Dockerfile` (`python:3.12-alpine`, `requirements.txt` copiado antes del código con `pip install --no-cache-dir`, usuario sin privilegios, sin secretos, arranque con migraciones + `uvicorn --host 0.0.0.0`, `HEALTHCHECK` a `127.0.0.1` sobre `/health/ready`) y `.dockerignore`
  - `env.example` con `DATABASE_URL` (sin valores) y `SQL_ECHO`
  - Fixes al TP solo si no arranca en el contenedor, anotados en `DEPLOY.md`
  - Sin Docker Compose; evidencia de build y healthcheck `healthy`
- **Conecta con**: no modifica C-01..C-07 ni el parcial; trabaja sobre una copia en `despliegue/` (DD-13).
- **Dependencias**: ninguna (usa el snapshot git; sin dependencia de código)
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica P11
  - `knowledge-base/07_flujos_principales.md` §Flujo P12
  - `knowledge-base/08_arquitectura_propuesta.md` §Variables de entorno (TP y despliegue), §Zip de entrega
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-13
  - `knowledge-base/10_preguntas_abiertas.md` §IN-07

### [C-16] `despliegue-vps`
- **Estado**: `[ ]` pendiente
- **Scope** (Ejercicio 10 parcial, 7 pts; US-124; casos D-01..D-08):
  - Build y run en el VPS con acceso a PostgreSQL del host (`host.docker.internal` / `--add-host=host.docker.internal:host-gateway`); `DATABASE_URL` por variable de entorno, nunca en la imagen
  - Migraciones y seed dentro del contenedor (`scripts/seed.py` del snapshot)
  - `DEPLOY.md` completo: URL pública, fecha/hora del despliegue, comandos exactos, cambios hechos al TP, procedimiento de actualización
  - `despliegue/evidencia/` con la salida de cada caso D-01..D-08
  - **Acciones manuales del usuario** (marcadas como tales en el propose): acceso SSH al VPS, credenciales, puertos, ejecución de los comandos y captura de evidencia; el agente prepara comandos y plantilla de `DEPLOY.md`
- **Conecta con**: solo `despliegue/` (DEPLOY.md, evidencia); no toca el código del parcial.
- **Dependencias**: `C-15`
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §Épica P12
  - `knowledge-base/07_flujos_principales.md` §Flujo P12
  - `knowledge-base/08_arquitectura_propuesta.md` §Variables de entorno, §Zip de entrega
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-13

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
| C-08 | settings-y-base-de-capas | P1 (6) | C-07 | ALTO | `[ ]` |
| C-09 | modulos-a-repositorios-uow | P6 (16) + P3 (8) | C-08 | ALTO | `[ ]` |
| C-10 | modelos-acceso-stock-migraciones | P2 (10) + P7 trigger | C-08 | CRITICO | `[ ]` |
| C-11 | autenticacion | P4 (14) + P7 intento | C-09, C-10 | CRITICO | `[ ]` |
| C-12 | autorizacion-roles-y-rutas | P5 (12) | C-11 | CRITICO | `[ ]` |
| C-13 | stock-movimientos-baja-logica-ventas | P6 parte 2 + P8 (6) | C-12, C-10 | ALTO | `[ ]` |
| C-14 | seed-casos-y-evidencia | transversal | C-13 | MEDIO | `[ ]` |
| C-15 | imagen-docker-tp-cap1a4 | P9 (11) | — | ALTO | `[ ]` |
| C-16 | despliegue-vps | P10 (7) | C-15 | ALTO | `[ ]` |

> Los ejercicios `P1..P10` son los del Parcial (6+10+8+14+12+16+10+6+11+7 = 100 pts); los numerados 1..7 son los del TP. Primer change pendiente recomendado: `C-08` (en paralelo, `C-15`).
