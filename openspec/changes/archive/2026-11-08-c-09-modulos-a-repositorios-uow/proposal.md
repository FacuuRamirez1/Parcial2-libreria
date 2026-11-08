# Proposal

## Why

Los servicios de los seis módulos de dominio (`editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`) reciben la sesión de base de datos directamente (`SessionDep`) y confirman con `session.commit()`. El Ejercicio 6 del parcial (repositorios y Unit of Work, 16 pts) exige reorganizar el acceso a datos en capas `Router → Service → UnitOfWork → Repository → Model`, donde los servicios reciben un `UnitOfWork`, los repositorios encapsulan las consultas (con precarga declarada dentro del método) y ninguna capa confirma por su cuenta. Sin este change, C-10/C-11/C-12/C-13 no pueden construir transacciones atómicas (RN-02, RN-10, RN-16) ni lecturas sin N+1 sobre repositorios.

## What Changes

- **Nuevo `app/modules/<modulo>/repository.py`** por módulo: un repositorio por entidad sobre `BaseRepository[T]` (o `SoftDeleteRepository[T]` cuando corresponda), con métodos específicos de búsqueda y conteo y la precarga (`joinedload`/`selectinload`) declarada dentro del método que la necesita.
- **Nuevo `app/modules/<modulo>/unit_of_work.py`** por módulo: `UnitOfWork` que compone el repositorio del módulo sobre una misma sesión; confirma al salir del bloque, revierte ante excepción, no cierra la sesión.
- **Refactor `service.py`** de los 6 módulos: reciben el `UnitOfWork` (no la sesión), lo abren con `async with` y nunca lo construyen ni confirman.
- **Refactor `router.py`** de los 6 módulos: construye el `UnitOfWork` mediante una dependencia que recibe la sesión de `get_session` y se lo pasa al servicio sin abrirlo.
- `schemas.py` se conserva (`extra="forbid"` en entrada, `exclude_unset` en PATCH, sin `password_hash` en salida); los listados pasan a devolver `{items,total,page,size,pages}` en lugar de `limit/offset` (DD-09).
- **Sin cambios de esquema**: `models.py` (C-02) no se toca; `migrations/` no se toca; `app/core/` no se modifica salvo documentar contratos.
- **Pruebas `.http`**: repetir los casos de `test/*.http` del TP contra el refactor (regresión) más paginación nueva, con respuesta esperada comentada.

## Capabilities

### New Capabilities

- `repositorios-editoriales`: `EditorialRepository(BaseRepository[Editorial])` con los métodos genéricos (`get_by_id`, `get_all`, `count`, `add`, `update`, `delete`) y escritura mediante `flush()`.
- `repositorios-generios`: `GeneroRepository(BaseRepository[Genero])` idéntico en forma a editoriales.
- `repositorios-autores`: `AutorRepository(BaseRepository[Autor])` idéntico en forma a editoriales.
- `repositorios-libros`: `LibroRepository(BaseRepository[Libro])` con búsqueda filtrada por `titulo` (`ILIKE` con parámetro ligado) y `genero_id`, conteo coherente, y precarga `joinedload` de editorial/género en listado y detalle.
- `repositorios-clientes`: `ClienteRepository(BaseRepository[Cliente])` con búsqueda por `email` y precarga de relaciones cuando corresponda.
- `repositorios-ventas`: `VentaRepository(BaseRepository[Venta])` con `get_con_detalle(id)` que precarga `cliente` (`joinedload`) y `renglones → libro` (`selectinload`) en un número fijo de consultas, más filtrado por `cliente_id`.
- `unit-of-work-modulos`: patrón de `UnitOfWork` por módulo (gestor de contexto async, commit al salir, rollback ante excepción, sin cerrar sesión) construido por dependencia en el router y abierto con `async with` en el servicio.

### Modified Capabilities

- Ninguna. La capacidad `paginacion` ya especifica `page ≥ 1`, `size` 1–100, `PaginatedResponse[T]` y 422 para página inexistente; C-09 alinea la implementación (`limit/offset` → `page/size`) a ese contrato sin cambiar sus requisitos.

## Impact

- **Código nuevo**: `repository.py` y `unit_of_work.py` en cada uno de los 6 módulos de dominio.
- **Código modificado**: `service.py` y `router.py` de los 6 módulos; `schemas.py` se conserva (posible ajuste de `response_model` de listados a `PaginatedResponse[T]`).
- **API**: los listados `GET /{modulo}` devuelven `{items,total,page,size,pages}`; `page` ≥ 1, `size` 1–100 (def. 20); página inexistente → 422; cero resultados = página vacía. Rutas de relación del TP conservadas (IN-04).
- **Base de datos**: ninguna (sin `create_all`, sin migraciones, sin cambios de esquema).
- **Dependencias**: ninguna nueva (usa `BaseRepository`/`SoftDeleteRepository`/`UnitOfWork` de `app/core`, esperados de C-08).
- **Changes posteriores**: C-10 usa `SoftDeleteRepository` sobre `Libro` (borrado lógico); C-11/C-12/C-13 usan el `UnitOfWork` para transacciones de registro, venta y eventos de seguridad.

## Open Questions

- `app/core/repository.py` y `app/core/unit_of_work.py` (`BaseRepository`, `SoftDeleteRepository`, `UnitOfWork`) son referenciados por C-08 pero no se hallaron en el snapshot restaurado: verificar que existan antes del apply; de lo contrario, crearlos es prerequisito de C-09 (sin cambiar su contrato).
- `app/core/paginacion.py` implementa hoy `limit/offset`; C-09 debe exponer `page/size` con propiedades `limit`/`offset` de compatibilidad (documentado como contrato, no como requisito nuevo de `paginacion`).
