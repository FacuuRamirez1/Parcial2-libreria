# Proposal

## Why

Los módulos de dominio creados en C-01 tienen `models.py` vacíos: no hay tablas que migrar (C-03) ni sobre las cuales construir contratos y CRUD (C-04+). El Ejercicio 2 de la consigna (25 pts, la épica de mayor peso; US-003) pide los 9 modelos de tabla con los nombres exactos de tablas y columnas, con la integridad garantizada **por la base** (UNIQUE, CHECK, FK) y con navegación en ambos extremos de cada relación, de modo que las reglas RN-01, RN-02, RN-03 y RN-09 y el requisito NF-04 (sin carga perezosa) tengan dónde apoyarse.

## What Changes

- Modelos de tabla SQLModel (`table=True`) en los `models.py` existentes de cada módulo funcional (`app/modules/<módulo>/models.py`; toda definición de dominio vive ahí), con `__tablename__` explícito:
  - `editoriales`: `Editorial` (`editorial`).
  - `generos`: `Genero` (`genero`).
  - `autores`: `Autor` (`autor`).
  - `libros`: `Libro` (`libro`) y `LibroAutor` (`libro_autor`, objeto de asociación con `rol` y `orden`, PK compuesta; **no** `link_model`).
  - `clientes`: `Cliente` (`cliente`) y `PerfilCliente` (`perfil_cliente`, uno a uno por `cliente_id` UNIQUE).
  - `ventas`: `Venta` (`venta`) y `RenglonVenta` (`renglon_venta`).
- Restricciones en la base: UNIQUE (`editorial.nombre`, `genero.nombre`, `libro.isbn`, `cliente.email`, `perfil_cliente.cliente_id`); CHECK (`precio > 0`, `stock >= 0`, `orden >= 1`, `rol` ∈ {autor, coautor, traductor, ilustrador}, `total >= 0`, `cantidad > 0`, `precio_unitario > 0`); claves foráneas; un índice por cada FK (`libro.editorial_id`, `libro.genero_id`, `libro_autor.autor_id`, `venta.cliente_id`, `renglon_venta.venta_id`, `renglon_venta.libro_id`).
- Dinero con `Decimal` → `NUMERIC(10,2)` (`libro.precio`, `renglon_venta.precio_unitario`) y `NUMERIC(12,2)` (`venta.total`); `venta.fecha` con zona horaria.
- Largo máximo físico en **todas** las columnas de texto (`VARCHAR(n)` vía `Field(max_length=n)`), con prioridad en claves y códigos: `isbn` 17, `email` 254, `rol` 20; el resto según la tabla de `design.md` D-08. La validación de los DTOs de C-04 queda como segunda capa.
- Relaciones `Relationship(back_populates=...)` en los dos extremos de cada FK; `Cliente.perfil` devuelve un objeto (`uselist=False`); `Libro.autorias[i].autor` como navegación del muchos a muchos con datos.
- Estrategia de carga declarada en cada relación para que **ninguna** lectura dispare carga perezosa: un acceso no precargado falla de inmediato en vez de emitir SQL oculto (la precarga con `joinedload`/`selectinload` la hacen las consultas de C-04+).
- Convención de nombres de restricciones e índices en `SQLModel.metadata` (nombres deterministas que Alembic pueda referenciar en `downgrade`), en `app/core/metadata.py`, que contiene **sólo** esa convención transversal; y un agregador fino `app/models.py` que **sólo** reexporta las 9 clases para Alembic y el seed (C-03), sin lógica ni definiciones de dominio.
- `Genero` y `Libro.genero_id` (FK nullable + índice + relación) quedan definidos de forma aislable, para que C-03 pueda generar la 2ª migración con sólo esos elementos.
- Criterio de aceptación definido como escenarios `.http` contra PostgreSQL 16 real, mapeados a los casos de prueba de la consigna (C-02..C-07) y a las restricciones que los respaldan. C-02 **no** crea archivos `.http`: como no tiene endpoints ni esquema (sin `create_all`; el esquema lo crea C-03), la tabla de escenarios de `design.md` D-11 es un traspaso: C-04 y C-05 escriben y ejecutan los `.http` (C-06 el de detalle sin N+1) y C-03 verifica el DDL real y las sondas de CHECK/largos tras `alembic upgrade head`. Durante el apply sólo corren chequeos locales sin base (importación, mappers, DDL compilado) como smoke opcional, no como aceptación. La base local `libreria` no se toca en C-02.

Fuera de alcance: migraciones Alembic y `scripts/seed.py` (C-03); DTOs `Create/Update/Read`, endpoints, registro de routers y traducción de `IntegrityError`/`DataError` a 409/422 (C-04); consultas con `joinedload`/`selectinload` (C-04..C-06); ejecución de los `.http` (C-04..C-06); `create_all` (prohibido, en cualquier base); `ON DELETE` en cascada en la base (no hay endpoints de borrado); tests automatizados (`pytest`).

## Capabilities

### New Capabilities
- `catalog-data`: tablas del catálogo (`editorial`, `genero`, `autor`, `libro`, `libro_autor`), sus restricciones de integridad, largos de texto y la navegación libro↔editorial, libro↔género y libro↔autor vía el objeto de asociación.
- `customer-data`: tablas `cliente` y `perfil_cliente`, la unicidad y el largo del email, y la relación uno a uno cliente↔perfil.
- `sales-data`: tablas `venta` y `renglon_venta`, montos en `Decimal`, fecha con zona horaria, la composición venta→renglones y las asociaciones con cliente y libro.
- `data-model-conventions`: reglas transversales de todos los modelos — nombres exactos de la consigna, modelos en su módulo funcional, texto siempre con largo máximo, convención de nombres de restricciones e índices, índice por cada FK, agregador único de modelos sin lógica de dominio, prohibición de carga perezosa, esquema creado sólo por migraciones y restricciones respaldando los casos de prueba de la consigna.

### Modified Capabilities
<!-- Ninguna: app-lifecycle y health no cambian de comportamiento. La regla "sin create_all" de app-lifecycle se mantiene y se reafirma en data-model-conventions. -->

## Impact

- **Código**: `app/modules/{editoriales,generos,autores,libros,clientes,ventas}/models.py` (de docstring a modelos reales; única ubicación de las definiciones de dominio); `app/core/metadata.py` nuevo (sólo convención de nombres); `app/models.py` nuevo (sólo imports/reexportación). Sin cambios en `main.py`, `database.py`, routers, schemas ni services.
- **Pruebas**: ningún archivo en `test/` en este change; los escenarios `.http` de aceptación quedan definidos en `design.md` D-11 y los escriben/ejecutan C-04 y C-05 (C-06 para el detalle).
- **API**: ninguno (no se agregan endpoints ni se registran routers).
- **Base de datos**: ninguno en este change (el esquema lo crea C-03 con Alembic). La base local `libreria` no se toca.
- **Dependencias**: ninguna nueva (`sqlmodel==0.0.48`, `sqlalchemy==2.1.8` ya fijadas).
- **Changes posteriores**: C-03 autogenera las dos migraciones desde este metadata (separando `genero`/`genero_id`) e inspecciona el DDL real; C-04 alinea los `max_length` de los DTOs con los largos de D-08 y traduce `DataError` (texto demasiado largo) a 422 con mensaje propio como red de seguridad; C-04..C-06 dependen de los nombres de relaciones (`autorias`, `perfil`, `renglones`, …) y ejecutan los escenarios `.http` de aceptación contra PostgreSQL 16.
- **Governance**: CRÍTICO (CHANGES.md). Todas las decisiones (las seis iniciales y las cinco preguntas abiertas) ya fueron resueltas por el usuario; ver `design.md` §Decisiones del usuario. No quedan preguntas abiertas.
