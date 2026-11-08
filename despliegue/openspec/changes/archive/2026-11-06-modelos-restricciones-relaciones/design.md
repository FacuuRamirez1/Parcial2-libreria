# Design

## Context

Estado actual (observado): C-01 dejó `app/core/{config,database}.py`, `app/main.py` (sólo registra `health`), `test/health.http` y los 6 módulos de dominio con `models.py` que contienen únicamente un docstring. `requirements.txt` fija `sqlmodel==0.0.48` y `sqlalchemy[asyncio]==2.1.8`; no hay Alembic (llega en C-03). Motivación y alcance: `proposal.md`. Requisitos observables: `specs/catalog-data`, `specs/customer-data`, `specs/sales-data`, `specs/data-model-conventions`.

Restricciones que condicionan el diseño:
- Nombres de tablas y columnas de la consigna son obligatorios (`knowledge-base/04_modelo_de_datos.md`); sólo se pueden **agregar** columnas.
- Estructura obligatoria por módulo funcional (consigna §Estructura obligatoria, `08_arquitectura_propuesta.md`): los modelos de tabla, restricciones y relaciones viven en `app/modules/<módulo>/models.py`; `LibroAutor` en `libros`, `PerfilCliente` en `clientes`, `RenglonVenta` en `ventas`.
- Reglas duras: sin `create_all`; dinero `Decimal`/`NUMERIC`; integridad en la base (DD-05), sin consultas previas; sin carga perezosa (NF-04).
- C-03 debe poder autogenerar una 1ª migración **sin** `genero` ni `libro.genero_id` y una 2ª que los agregue (CHANGES.md C-02/C-03).
- Verificación: la consigna exige archivos `.http` en `test/` que demuestren los casos C-01..C-08 contra una instancia real de PostgreSQL 16. Este change **no** expone endpoints ni crea el esquema (eso es C-03 con Alembic), así que la aceptación de sus restricciones se define aquí pero se **ejecuta** en changes posteriores (ver D-11).
- Hechos verificados con un prototipo descartable (fuera del repo, sin base) sobre las versiones fijadas: la convención de nombres se aplica a PK/UQ/CK/FK/IX; `Field(max_digits, decimal_places)` produce `NUMERIC(p, s)`; `Field(max_length=n)` en un `str` produce `VARCHAR(n)` (`AutoString(length=n)`); un campo `datetime` produce `TIMESTAMP WITH TIME ZONE` (tipo `UTCDateTime` de SQLModel ≥ 0.0.45); `Field(unique=True)` genera una restricción `UNIQUE` nombrada; `lazy="raise"` no impide `back_populates` sobre objetos nuevos.

## Goals / Non-Goals

**Goals:**
- Un metadata completo, determinista y auto-contenido que C-03 pueda autogenerar sin correcciones de nombres.
- Límites físicos de texto en la base (`VARCHAR(n)`) como primera garantía de tamaño, con los DTOs de C-04 como segunda capa.
- Nombres de relaciones estables que C-04..C-06 usarán en `joinedload`/`selectinload`.
- Que un olvido de precarga falle ruidosamente en desarrollo, no en silencio.
- Que cada caso de prueba de la consigna que depende del esquema tenga una restricción nombrada que lo respalde y un escenario `.http` planificado.

**Non-Goals:**
- `ON DELETE` en la base y cascadas de borrado (no hay endpoints `DELETE`).
- Validaciones de **formato** (email válido, dígito verificador del ISBN): son de los DTOs de C-04.
- Restricciones no pedidas por la consigna (p. ej. `UNIQUE(libro_id, orden)`, `UNIQUE(autor.nombre)`), tipos `ENUM` nativos, columnas de auditoría (DD-02: nada fuera de la rúbrica).
- Mixins/clases base compartidas entre DTOs y tablas (los DTOs se diseñan en C-04).
- Ejecutar escrituras reales contra PostgreSQL dentro de C-02 (no hay esquema hasta C-03).

## Decisions

### D-01 — Cada modelo vive en su módulo funcional, con `__tablename__` explícito
| Módulo | Clases (tabla) |
|---|---|
| `app/modules/editoriales/models.py` | `Editorial` (`editorial`) |
| `app/modules/generos/models.py` | `Genero` (`genero`) |
| `app/modules/autores/models.py` | `Autor` (`autor`) |
| `app/modules/libros/models.py` | `Libro` (`libro`), `LibroAutor` (`libro_autor`) |
| `app/modules/clientes/models.py` | `Cliente` (`cliente`), `PerfilCliente` (`perfil_cliente`) |
| `app/modules/ventas/models.py` | `Venta` (`venta`), `RenglonVenta` (`renglon_venta`) |

Toda definición de dominio (columnas, tipos, largos, UNIQUE, CHECK, FK, índices, relaciones) está **sólo** en estos 6 archivos. `__tablename__` se declara en las 9 clases: SQLModel derivaría `libroautor`, `perfilcliente`, `renglonventa` de los nombres de clase, que **no** son los de la consigna. Declararlo también en las simples evita depender de la regla implícita.

Referencias entre módulos: anotaciones de relación como cadenas (`"Editorial"`) con imports bajo `if TYPE_CHECKING:` (patrón de SQLModel para varios archivos), para evitar imports circulares. **No** se usa `from __future__ import annotations` (SQLModel necesita evaluar las anotaciones de campos).

*Alternativas*: un único archivo con las 9 tablas (rompe la estructura por módulo que exige la consigna). Descartada.

### D-02 — Columnas y tipos
- PK: `id: int | None = Field(default=None, primary_key=True)` → `SERIAL` (entero autoincremental). `libro_autor` no tiene `id`: PK compuesta `libro_id` + `autor_id` (`primary_key=True` en ambas, cada una con `foreign_key`).
- Texto: `str` con `Field(max_length=n)` → `VARCHAR(n)`; los largos están en D-08. Ninguna columna de texto queda sin largo.
- Dinero: `Decimal` con `Field(max_digits=10, decimal_places=2)` (`libro.precio`, `renglon_venta.precio_unitario`) y `max_digits=12` (`venta.total`) → `NUMERIC(10,2)` / `NUMERIC(12,2)` (fijados por la consigna).
- Fecha: `venta.fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))` → `TIMESTAMP WITH TIME ZONE`. **No** se usa `sa_type=DateTime(timezone=True)`: la skill `sqlmodel` indica que eso anula el tipo `UTCDateTime` que normaliza a UTC.
- Enteros: `stock`, `orden`, `cantidad` → `INTEGER`.
- Nulabilidad: todas las columnas `NOT NULL` excepto `libro.genero_id` (D-09, aprobada).
- `venta.total` sin valor por defecto: lo calcula y asigna el service de C-05 (RN-07).

### D-03 — Restricciones en `__table_args__` con nombres cortos + convención de nombres global
- UNIQUE de una columna: `Field(unique=True)` (`editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email`, `perfil_cliente.cliente_id`).
- CHECK: `CheckConstraint("<expr>", name="<corto>")` en `__table_args__`:
  - `libro`: `precio > 0` (`precio_positivo`), `stock >= 0` (`stock_no_negativo`).
  - `libro_autor`: `orden >= 1` (`orden_positivo`), `rol IN ('autor', 'coautor', 'traductor', 'ilustrador')` (`rol_valido`).
  - `venta`: `total >= 0` (`total_no_negativo`).
  - `renglon_venta`: `cantidad > 0` (`cantidad_positiva`), `precio_unitario > 0` (`precio_unitario_positivo`).
- Convención de nombres asignada a `SQLModel.metadata.naming_convention` **antes** de declarar cualquier tabla (D-04):
  ```
  pk: pk_%(table_name)s
  fk: fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
  uq: uq_%(table_name)s_%(column_0_name)s
  ck: ck_%(table_name)s_%(constraint_name)s
  ix: ix_%(column_0_label)s
  ```
  Resultado (verificado): `ck_libro_precio_positivo`, `fk_libro_genero_id_genero`, `uq_perfil_cliente_cliente_id`, `ix_libro_editorial_id`. El nombre más largo (`ck_renglon_venta_precio_unitario_positivo`, 41) entra en el límite de 63 de PostgreSQL.

**Por qué**: sin convención, PostgreSQL inventa los nombres de FK/UNIQUE/CHECK y Alembic autogenera `op.drop_constraint(None, ...)` en el `downgrade` de la 2ª migración, que falla. Con nombres deterministas, `downgrade -1` de C-03 funciona sin edición manual. Además, C-04 puede mapear `IntegrityError` → mensaje propio por nombre de restricción sin exponerlo (RN-12), y cada caso `.http` de D-11 se ata a un nombre concreto.

*Alternativas*: nombrar cada restricción a mano (las FK de `Field(foreign_key=...)` no aceptan nombre sin bajar a `sa_column_args`; más ruido); dejar nombres de PostgreSQL (rompe `downgrade` autogenerado). CHECK de `rol` vs tipo `ENUM` nativo: se elige CHECK porque la consigna lo pide como CHECK y un `ENUM` complica migraciones (ALTER TYPE) sin aporte para la rúbrica.

### D-04 — `app/core/metadata.py`: sólo la convención de nombres transversal
Nuevo módulo `app/core/metadata.py` que contiene **únicamente** el diccionario `CONVENCION_NOMBRES` (D-03) y su asignación a `SQLModel.metadata.naming_convention`. No contiene ni importa nada de dominio (ninguna tabla, columna, restricción ni módulo de `app/modules/`), ni FastAPI, ni la configuración: importar modelos no exige `.env`. Es infraestructura transversal, del mismo tipo que `config.py` y `database.py` en `app/core/`.

Cada `models.py` de dominio empieza con `import app.core.metadata  # noqa: F401` y un comentario (la convención debe existir antes de declarar tablas). La dependencia va de los módulos hacia `core`, nunca al revés; es idempotente.

**Por qué no rompe la estructura modular**: `app/core/` ya es, por la consigna, el lugar de lo transversal (configuración, motor, sesión). Una convención de nombres que aplica igual a las 9 tablas es transversal por definición; ponerla en un módulo de dominio la haría depender de uno arbitrario, y repetirla en los 6 es duplicación con riesgo de divergencia.

*Alternativas*: en `app/core/database.py` (mezcla motor/sesión con esquema y arrastra FastAPI —`from fastapi import Depends, Request`— al importar modelos desde scripts y migraciones); en `app/modules/__init__.py` (funciona porque Python importa el paquete padre primero, pero es implícito y frágil).

### D-05 — `app/models.py`: agregador fino de imports, sin lógica de dominio
Nuevo módulo `app/models.py` que **sólo** importa las 9 clases desde los 6 `app/modules/<módulo>/models.py` y las reexporta en `__all__`. No define clases, columnas, restricciones, relaciones ni funciones; no tiene lógica. Existe porque Alembic (`migrations/env.py`, C-03) y `scripts/seed.py` (C-03) necesitan que **todas** las tablas estén registradas en `SQLModel.metadata` y que las relaciones por cadena se resuelvan; con un único punto de importación, olvidar un módulo es imposible (un olvido haría que `--autogenerate` proponga borrar tablas). `genero` se importa en una línea propia para que C-03 pueda excluirla temporalmente (D-10).

**Por qué no centraliza código de dominio**: la fuente de verdad de cada tabla sigue en su módulo (D-01); `app/models.py` es una lista de imports, el equivalente para el esquema de lo que `app/main.py` ya hace para los routers (la raíz de `app/` compone los módulos). Agregar o cambiar una columna nunca toca este archivo; sólo se toca al agregar una tabla nueva.

*Alternativas de ubicación (igual de simples)*:
- `migrations/env.py` importando módulo por módulo: válido, pero `scripts/seed.py` tendría que repetir la lista (dos listas que pueden divergir).
- `app/modules/__init__.py`: obligaría a cargar todos los modelos ante cualquier import de un submódulo (efecto lateral implícito).
- `app/core/registro_modelos.py`: `core` pasaría a conocer los módulos de dominio, contradiciendo D-04 (`core` sin nada de dominio).

Se elige `app/models.py` por ser explícito, único y simétrico con `main.py`. **Decidido por el usuario**: se mantiene `app/models.py` como agregador fino (ver §Decisiones del usuario, 2).

### D-06 — Relaciones con `back_populates` en ambos extremos y nombres estables
| Lado A | Lado B | Tipo |
|---|---|---|
| `Editorial.libros: list[Libro]` | `Libro.editorial: Editorial` | 1–N |
| `Genero.libros: list[Libro]` | `Libro.genero: Genero \| None` | 0..1–N |
| `Libro.autorias: list[LibroAutor]` (orden por `LibroAutor.orden`) | `LibroAutor.libro: Libro` | 1–N (composición de la autoría) |
| `Autor.autorias: list[LibroAutor]` | `LibroAutor.autor: Autor` | 1–N |
| `Cliente.perfil: PerfilCliente \| None` (`uselist=False`) | `PerfilCliente.cliente: Cliente` | 1–0..1 |
| `Cliente.ventas: list[Venta]` | `Venta.cliente: Cliente` | 1–N |
| `Venta.renglones: list[RenglonVenta]` (orden por `RenglonVenta.id`) | `RenglonVenta.venta: Venta` | 1–N (composición) |
| `Libro.renglones: list[RenglonVenta]` | `RenglonVenta.libro: Libro` | 1–N |

- `LibroAutor` es entidad propia (objeto de asociación); **no** hay atajo `Libro.autores` con `link_model`/`secondary` (la consigna pide navegar `libro.autorias[i].autor`; un segundo camino sobre la misma tabla obliga a `viewonly` y confunde las escrituras).
- `uselist=False` se declara explícitamente en `Cliente.perfil` aunque SQLModel lo infiere de la anotación no-lista, porque CHANGES.md lo pide y documenta la intención.
- `order_by` en `Libro.autorias` y `Venta.renglones` (vía `sa_relationship_kwargs`) da orden estable a las respuestas de C-04/C-05 sin `ORDER BY` en cada consulta; aplica también a `selectinload` (aprobado).
- Cascadas ORM (sólo a nivel sesión, no en la base): `Venta.renglones`, `Libro.autorias` y `Cliente.perfil` con `cascade="all, delete-orphan"` (composición: el hijo no existe sin el padre y se guarda al agregar el padre, RN-04; aprobado). El resto con la cascada por defecto (`save-update, merge`).

### D-07 — Sin carga perezosa: `lazy="raise"` en las 16 relaciones (aprobado)
Cada `Relationship` lleva `sa_relationship_kwargs={"lazy": "raise", ...}`. Un acceso a una relación no precargada lanza `InvalidRequestError` inmediatamente, sin emitir SQL; las opciones `joinedload`/`selectinload` de cada consulta lo sobrescriben. Verificado que no bloquea `back_populates` sobre objetos nuevos (armar una venta con sus renglones antes del `commit`).

**Por qué**: con sesión asíncrona la carga perezosa por defecto (`select`) falla igual, pero con un `MissingGreenlet` críptico y a veces sólo en ciertos caminos; con `raise` el error es claro y el corrector ve que la estrategia está **declarada**. Cumple NF-04 literalmente: es imposible una lectura perezosa.

*Alternativas*: `lazy="select"` por defecto (deja posible el N+1 en contextos síncronos y el error asíncrono es opaco); `lazy="selectin"`/`"joined"` en el modelo (precarga siempre y contradice "declarados en la misma consulta"); `lazy="raise_on_sql"` (más sutil de explicar).

*Consecuencia para C-04/C-05*: no se puede asignar `cliente.perfil = ...` ni hacer `libro.autorias.append(...)` sobre un objeto **persistente** sin haber precargado la colección; las altas deben construir el hijo con la FK (`PerfilCliente(cliente_id=...)`) o el padre nuevo con sus hijos. Se deja anotado para esos changes.

### D-08 — Largos máximos físicos en todas las columnas de texto (aprobado con reserva: `VARCHAR(n)`)
Decisión revisada a pedido del usuario: la base impone un límite físico a **todo** texto con `Field(max_length=n)` → `VARCHAR(n)`. Ni la consigna ni la KB fijan largos (revisado: `TP_Cap1a4_Consigna.pdf` §Modelo de dominio y `04_modelo_de_datos.md` sólo fijan tipos numéricos); los valores siguientes son decisión de este change, con criterio "cubrir holgadamente el dato real más largo razonable sin dejar el campo abierto":

| Columna | Largo | Criterio |
|---|---|---|
| `libro.isbn` | `VARCHAR(17)` | Clave crítica. ISBN-13 con guiones mide 17 (`978-950-00-0006-6`, ejemplo de la consigna); ISBN-10 con guiones, 13. No se normaliza el formato: se guarda como lo envía el DTO. |
| `cliente.email` | `VARCHAR(254)` | Clave crítica. Máximo práctico de una dirección según RFC 5321 (camino de 256 menos los `< >`); largo estándar de la industria. |
| `libro_autor.rol` | `VARCHAR(20)` | Código crítico. El valor más largo permitido por el CHECK es `ilustrador` (10); 20 deja margen para un rol nuevo sin cambiar el tipo (sólo el CHECK). |
| `editorial.nombre` | `VARCHAR(120)` | Clave UNIQUE; nombres comerciales largos ("Editorial Sudamericana / Penguin Random House" ≈ 45) con amplio margen. |
| `genero.nombre` | `VARCHAR(60)` | Clave UNIQUE; un género es una o pocas palabras ("Ciencia ficción" 15, "Literatura infantil y juvenil" 29). |
| `editorial.pais` | `VARCHAR(60)` | Nombre de país; el más largo en castellano de uso común ronda 50 ("Reino Unido de Gran Bretaña e Irlanda del Norte", 47). |
| `autor.nombre` | `VARCHAR(120)` | Nombre completo de persona, igual que `cliente.nombre`. |
| `autor.nacionalidad` | `VARCHAR(60)` | Mismo criterio que `pais`. |
| `libro.titulo` | `VARCHAR(255)` | Títulos con subtítulo pueden ser largos; 255 es el tope convencional y deja lugar a títulos reales extensos. |
| `cliente.nombre` | `VARCHAR(120)` | Nombre y apellidos compuestos. |
| `perfil_cliente.telefono` | `VARCHAR(30)` | E.164 son 15 dígitos; con `+`, espacios, guiones e interno (`+54 9 11 1234-5678 int. 12`) entra en 30. Texto, no número (ceros iniciales, `+`). |
| `perfil_cliente.direccion` | `VARCHAR(255)` | Calle, número, piso, departamento y localidad en una línea. |

**Por qué**: el usuario pide límites físicos en la base; además, es coherente con DD-05 (delegar en la base lo que la base puede garantizar) y evita que un cliente que saltee la API (psql, seed) cargue textos arbitrarios.

**Dos capas**: los DTOs de C-04 validan `max_length` (mismo valor o menor) y formato, y responden 422 **antes** de llegar a la base; `VARCHAR(n)` es la segunda capa. Observación técnica: en modelos `table=True` SQLModel **no** valida al construir el objeto, así que `max_length` en la tabla sólo afecta al DDL; la validación de entrada sigue siendo responsabilidad del DTO.

*Consecuencia para C-04*: si un texto excede el largo y no lo frenó el DTO, PostgreSQL lanza `DataError` (`StringDataRightTruncation`), **no** `IntegrityError`. **Decidido por el usuario**: la tabla de largos queda aprobada tal cual, y C-04 debe (a) usar en cada DTO `max_length` ≤ el de la columna (importar la misma constante o repetir el número con referencia a esta tabla) y (b) traducir también `DataError` a un 422 con mensaje propio, sin texto interno de la base (RN-12), como red de seguridad.

*Alternativa descartada*: texto sin largo (`VARCHAR` sin `n`), versión anterior de esta decisión; rechazada por el usuario.

### D-09 — Nulabilidad: todo obligatorio salvo `libro.genero_id` (aprobado)
La KB sólo marca como opcional `libro.genero_id`. Se toman como `NOT NULL` también `editorial.pais`, `autor.nacionalidad`, `perfil_cliente.telefono` y `perfil_cliente.direccion`. Es la lectura mínima de la consigna; relajar a NULL más adelante es una migración trivial, endurecer con datos existentes no.

### D-10 — Aislamiento de `Genero` / `libro.genero_id` para C-03
Todo lo relativo al género queda en elementos separables: la clase `Genero` en su módulo, y en `Libro` exactamente dos atributos contiguos y marcados con un comentario (`genero_id` con `foreign_key`, `nullable` e `index=True`, y la relación `genero`), más `Genero.libros`. Ninguna restricción CHECK ni índice compuesto mezcla `genero_id` con otras columnas. C-03 decide el mecanismo concreto para excluirlos en la 1ª autogeneración (p. ej. comentar temporalmente esos atributos y la importación en `app/models.py`); C-02 sólo garantiza que esa exclusión no rompa ninguna otra tabla ni relación.

### D-11 — Estrategia de verificación: aceptación por `.http` contra PostgreSQL 16 real, traspasada a C-03/C-04/C-05/C-06; chequeos locales sólo como smoke opcional
**Decisión revisada** (el usuario rechazó "verificación exclusivamente con `python -c`"). La consigna exige `test/*.http` que demuestren los casos C-01..C-08 contra una instancia real de PostgreSQL 16, y ése es el criterio de aceptación de las restricciones de este change.

**Tensión, explicitada**: en C-02 no hay endpoints (los routers de dominio llegan en C-04/C-05) ni esquema en la base (las reglas duras prohíben `create_all`; las tablas sólo las crea `alembic upgrade head` en C-03). Por lo tanto **ningún `.http` puede ejercitar estos modelos dentro de C-02**. **Decidido por el usuario**: C-02 no crea ningún archivo `.http` (ni esqueleto); la aceptación se *define* aquí (tabla de (a)) y se *traspasa*: los escenarios `.http` los escribe y ejecuta C-04/C-05 (C-06 el de detalle), y las verificaciones a nivel de base las hace C-03.

**(a) Criterio de aceptación — escenarios `.http` contra PostgreSQL 16 real**

Cada restricción del esquema queda atada a un escenario `.http` (con la respuesta esperada en un comentario, como pide la consigna) y al change que lo vuelve ejecutable:

| Escenario `.http` | Caso consigna | Restricción de C-02 que lo respalda | Esperado | Ejecutable desde |
|---|---|---|---|---|
| `POST /clientes/` con email repetido | C-02 | `uq_cliente_email` | 409 mensaje propio | C-04 |
| `POST /libros/` con ISBN repetido | C-02 | `uq_libro_isbn` | 409 mensaje propio | C-04 (alta simple) / C-05 (alta con autores) |
| `POST /clientes/{id}/perfil` dos veces | C-03 | `uq_perfil_cliente_cliente_id` | 409 | C-05 |
| `POST /libros/` con `editorial_id` inexistente | C-04 | `fk_libro_editorial_id_editorial` | 409 mensaje propio | C-05 |
| `POST /libros/` con `autor_id` inexistente | C-04 | `fk_libro_autor_autor_id_autor` | 409 mensaje propio | C-05 |
| `POST /ventas/` con `cliente_id` inexistente | C-05 | `fk_venta_cliente_id_cliente` | 409 | C-05 |
| `POST /ventas/` con `libro_id` inexistente | C-05 | `fk_renglon_venta_libro_id_libro` (respaldo; ver nota) | 409 | C-05 |
| `POST /ventas/` válida con dos renglones | C-06 | composición `Venta.renglones` (cascade), `NUMERIC(10,2)`/`(12,2)`, `fecha` con zona | 201, renglones creados, precios copiados, total calculado | C-05 |
| `GET /libros/{id}` y `GET /ventas/{id}` | C-07 | relaciones `autorias`/`renglones` con `order_by`, `lazy="raise"` | 200, cantidad fija de consultas en consola | C-06 |
| Complementarios (no mínimos): `POST /editoriales/` y `POST /generos/` con nombre repetido | — | `uq_editorial_nombre`, `uq_genero_nombre` | 409 | C-04 |
| Complementario: `POST /libros/` con `genero_id` inexistente | — | `fk_libro_genero_id_genero` | 409 | C-05 |
| Complementarios: `precio = 0`, `stock = -1`, `rol = 'editor'`, `orden = 0`, `cantidad = 0`, texto más largo que la columna | — | CHECK y `VARCHAR(n)` (segunda capa) | 422 desde el DTO | C-04 / C-05 |

Notas honestas sobre lo que el `.http` puede y no puede demostrar:
- Los casos C-01 (path no entero) y C-08 (inyección en búsqueda) no dependen de este change.
- Para CHECK y `VARCHAR(n)`, el DTO responde 422 antes de llegar a la base (RN-03: "CHECK en la base **y** validación del DTO"); un `.http` demuestra la primera capa, no la restricción física. La restricción física se demuestra en C-03 (ver (c)).
- Para "venta con libro inexistente", C-05 lee el precio del libro antes de insertar (RN-06), así que el 409 puede venir del service; la FK es la garantía de respaldo.

**(b) Qué se crea en `test/` en C-02: nada**

**Decidido por el usuario**: C-02 no crea `test/restricciones.http` ni esqueleto alguno. Los escenarios de la tabla (a), cada uno con su caso de la consigna, su restricción y el change que lo vuelve ejecutable, son el traspaso: C-04 escribe y ejecuta los marcados "C-04", C-05 los marcados "C-05" y C-06 los marcados "C-06", contra PostgreSQL 16 real y con la respuesta esperada en un comentario; C-07 los consolida con los `.http` finales (CHANGES.md).

**(c) Verificación contra PostgreSQL 16 real del DDL, traspasada a C-03**

En C-03, tras `alembic upgrade head` sobre una base vacía, se inspecciona el esquema real (`\d+ <tabla>` en psql o `information_schema`/`pg_constraint`) y se comprueban: las 9 tablas, cada nombre de restricción/índice de D-03, los `VARCHAR(n)` de D-08, `NUMERIC`, `TIMESTAMPTZ` y nulabilidad. Las restricciones que el DTO oculta (CHECK, `VARCHAR(n)`) se prueban con `INSERT` directos dentro de `BEGIN … ROLLBACK` (nunca por `create_all`).

**Decidido por el usuario (opción A)**: esas sondas corren sobre la base `libreria` de desarrollo, dentro de transacciones que se revierten; no se crea una base descartable (`libreria_verif`). Salvaguardas obligatorias: (1) sólo después de `alembic upgrade head`; (2) siempre `BEGIN` explícito y `ROLLBACK` al final, nunca `COMMIT`; (3) sin datos residuales (verificar conteos antes y después). Precondición conocida: las tablas locales preexistentes en `libreria` (no creadas por Alembic) entran en conflicto con la migración y deben borrarse y recrearse antes de C-03.

**(d) Chequeos locales sin base — smoke opcional del desarrollador, NO criterio de aceptación**

Durante el apply de C-02, el desarrollador puede (y se recomienda) correr con el intérprete del `.venv`, sin `DATABASE_URL` y sin conexión: importar `app.models` + `configure_mappers()`; listar `SQLModel.metadata.tables`; compilar el DDL con `CreateTable(t).compile(dialect=postgresql.dialect())` (generación de texto SQL, **no** ejecuta nada ni usa `create_all`); inspeccionar `Relationship.property` (`lazy`, `uselist`, `cascade`, `order_by`). Sirven como ciclo rápido "falla sobre el `models.py` vacío → implementar → pasa" (adaptación del Strict TDD, sin archivos de test extra), y su salida se adjunta al resumen del apply como evidencia. **No** sustituyen a (a) ni a (c). No se usa `create_all` en ninguna base, ni siquiera descartable.

**Resumen: qué se verifica cuándo**

| Momento | Qué | Cómo | Contra |
|---|---|---|---|
| C-02 (apply) | Importación, mappers, nombres, tipos y largos en el DDL compilado, relaciones | Smoke opcional (d) | Sin base |
| C-02 (apply) | Escenarios de aceptación definidos (sin archivo `.http`) | Tabla de (a), traspaso a C-03..C-06 | — |
| C-03 | DDL real: tablas, restricciones, índices, `VARCHAR(n)`, tipos; CHECK/largos con `INSERT` + `ROLLBACK` | psql / catálogo tras `alembic upgrade head` (c), sobre `libreria` con las salvaguardas de (c) | PostgreSQL 16 real |
| C-04 | 409 por UNIQUE de email/ISBN/nombres; 422 de DTO | `.http` | PostgreSQL 16 real |
| C-05 | 409 por UNIQUE de perfil y FK; 201 de venta con renglones | `.http` | PostgreSQL 16 real |
| C-06 | Detalle sin N+1 (cantidad fija de consultas) | `.http` + consola `SQL_ECHO` | PostgreSQL 16 real |

*Alternativas descartadas*: verificación sólo con `python -c` (rechazada por el usuario: no es el criterio de la consigna); pytest (fuera de la política del proyecto, C-01 D-06); `create_all` en una base temporal para probar escrituras en C-02 (regla dura; además duplicaría lo que C-03 hace con Alembic); adelantar a C-02 un router "de prueba" (endpoints fuera de alcance, no pedidos).

## Risks / Trade-offs

- [`lazy="raise"` puede romper código de C-04+ que acceda a relaciones sin precargar, incluso en `response_model` si un DTO incluye un campo de relación] → es el comportamiento buscado; los DTOs de lectura con relaciones se construyen desde consultas con `joinedload`/`selectinload`. Documentado en D-07.
- [Un texto más largo que la columna produce `DataError`, no `IntegrityError`; si el DTO de C-04 tiene un `max_length` mayor, el usuario recibe un 500] → C-04 alinea los `max_length` con D-08 y traduce `DataError` a 422 con mensaje propio (decidido).
- [La aceptación por `.http` de este change ocurre recién en C-03..C-06; un defecto del modelo puede descubrirse tarde] → el smoke (d) cubre lo verificable sin base durante el apply, y C-03 inspecciona el DDL real antes de que C-04 escriba endpoints.
- [Las sondas `INSERT … ROLLBACK` de C-03 corren sobre la base de desarrollo `libreria`; un `COMMIT` accidental dejaría datos residuales] → salvaguardas de D-11 (c): sólo tras `alembic upgrade head`, `BEGIN`/`ROLLBACK` explícitos, nunca `COMMIT`, conteos antes/después.
- [Alembic autogenerate renderiza `sqlmodel.sql.sqltypes.AutoString(length=n)` y `UTCDateTime()`, que requieren `import sqlmodel` en la migración] → riesgo de C-03: agregar `import sqlmodel` en `script.py.mako`. Se deja anotado.
- [`venta.fecha` tiene valor por defecto sólo en Python, no `server_default`] → los inserts por fuera de la app (psql, sondas de C-03) deben dar la fecha; el seed es Python (DD-04) y usa los modelos.
- [Sin `ON DELETE CASCADE`, borrar a mano un cliente con ventas en psql falla por FK] → deseable (RN-08) y no hay endpoints de borrado.
- [Cambiar la convención de nombres o un largo después de C-03 obligaría a una migración] → convención y largos se fijan ahora; ampliar un `VARCHAR` es una migración trivial, achicarlo no.
- [Anotaciones por cadena entre módulos: un error tipográfico sólo aparece al configurar mappers] → el smoke (d) ejecuta `configure_mappers()`, y C-03 lo ejecuta de todos modos al importar `app.models` en `env.py`.

## Migration Plan

No aplica a la base en este change (el esquema lo crea C-03). Rollback: revertir el commit; los `models.py` vuelven a ser sólo docstring y se borran `app/core/metadata.py` y `app/models.py`.

## Decisiones del usuario

Resueltas antes: D-07 (`lazy="raise"`), D-09 (nulabilidad) y D-06 (cascadas y `order_by`) aprobadas; D-08 (largos) y D-04/D-05 (archivos nuevos) aprobadas con reservas e incorporadas arriba; D-11 rechazada en su versión anterior y reescrita.

Las cinco preguntas abiertas quedaron resueltas por el usuario:

1. **Esqueleto `test/restricciones.http`**: NO se crea en C-02. Los escenarios `.http` los escriben C-04 y C-05 (C-06 el de detalle), cada uno mapeado en D-11 (a) a su caso de la consigna, su restricción y el change que lo vuelve ejecutable; la verificación a nivel de base queda en C-03. Reflejado en D-11 (b), proposal, specs y tasks.
2. **Ubicación del agregador**: se mantiene `app/models.py` como agregador fino (sin cambios al diseño, D-05).
3. **Base para las sondas `INSERT … ROLLBACK` de C-03**: opción A, la base `libreria` de desarrollo dentro de transacciones revertidas; sin base descartable. Salvaguardas: sólo tras `alembic upgrade head`, `BEGIN` explícito y `ROLLBACK`, nunca `COMMIT`, sin datos residuales. Las tablas locales preexistentes en `libreria` que conflictúan con Alembic deben borrarse y recrearse antes de C-03 (problema conocido). Ver D-11 (c).
4. **`DataError` en C-04**: sí, C-04 lo traduce a 422 con mensaje propio como red de seguridad (además de DTOs con `max_length` ≤ D-08). Ver D-08.
5. **Largos de D-08**: tabla aprobada tal cual.

## Open Questions

Ninguna.

Diferibles (no cambian este change):
- Mecanismo exacto de exclusión temporal de `genero` en la 1ª autogeneración → C-03.
- Discrepancia detectada fuera de alcance: `02_descripcion_general.md` dice que `GET /health/ready` responde siempre 200, mientras el spec archivado `health` de C-01 define 503 con la base caída (el `test/health.http` actual documenta 200). No afecta a C-02; conviene alinearlo en la KB o en C-07.
