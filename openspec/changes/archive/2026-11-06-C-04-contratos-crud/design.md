# Design

## Context

Estado actual (observado): C-03 (según el usuario, ya implementado y commiteado) dejó `app/core/repository.py` (`BaseRepository`, `SoftDeleteRepository`), `app/core/unit_of_work.py` (`UnitOfWork`), `app/core/database.py` (`crear_motor`, `crear_fabrica_sesiones`, `get_session`, `SessionDep`), `app/main.py` (registra solo `health`), `test/health.http` y los 6 módulos de dominio con `models.py` reales (tablas con restricciones y relaciones) y `schemas.py`/`service.py`/`router.py` con solo docstring o esqueleto de router. Motivación y alcance: `proposal.md`. Requisitos observables: `specs/paginacion/`, `specs/contratos-editoriales/`, `specs/contratos-generos/`, `specs/contratos-autores/`, `specs/contratos-libros/`, `specs/contratos-clientes/`, `specs/contratos-ventas/`, `specs/endpoints-crud/`, `specs/repositorios-modulo/`, `specs/handler-integridad-global/`.

Restricciones que condicionan el diseño:
- Reglas duras (`AGENTS.md`): nunca `create_all`; nunca `float` para dinero (solo `Decimal`); nunca pre-consultar unicidad/existencia de ids (dejar que UNIQUE/FK rechacen y responder 409); nunca devolver texto interno de la base (traducir `IntegrityError` a mensaje propio); nunca carga perezosa (`joinedload`/`selectinload` en la misma consulta); todo handler `async def`; sin credenciales en el código.
- Stack: Python 3.12, FastAPI, SQLModel, SQLAlchemy 2 async, asyncpg, PostgreSQL 16.
- Todos los DTOs de entrada con `ConfigDict(extra="forbid")`.
- Salida de usuario sin `password_hash` (ocultar de toda respuesta).
- `DELETE /libros/{id}` → 204 con soft delete (`borrado_en`), sin borrado físico.
- Sin `PATCH` para ventas.
- `POST` por recurso → 201 al crear.

## Goals / Non-Goals

**Goals:**
- Contratos de entrada/salida separados de los modelos de tabla, con `extra="forbid"` en entrada.
- Paginación estándar genérica y reutilizable por todos los listados.
- Endpoints CRUD con códigos exactos (201, 404, 409, 422) y mensajes propios.
- Soft delete de libros sin endpoint PATCH en ventas.
- Repositorios específicos por módulo con cargas anticipadas donde corresponda.
- Handler global que traduce `IntegrityError` a 409 sin texto de la base.
- Archivos `test/*.http` con respuesta esperada comentada para cada endpoint.

**Non-Goals:**
- Lógica de transacción y altas con relaciones (C-05).
- `POST /libros/` con autores (crear `LibroAutor`) — ese endpoint de alta completa vive en C-05; en C-04 el `POST /libros/` crea el libro simple y el service de C-05 lo extiende.
- Consultas con `joinedload`/`selectinload` en listados de libros (C-06).
- Aviso de comprobante con `BackgroundTasks` (C-07).
- Tests automatizados (`pytest`); `create_all` en cualquier base.

## Decisions

### D-01 — `app/core/paginacion.py`: `PaginatedResponse[T]` y cálculo de páginas

Modelo Pydantic genérico:
```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int
```
- `page` ≥ 1, default 1; `size` de 1 a 100, default 20 (validado con `Field(ge=1, le=100)`).
- Función `calcular_paginas(total: int, size: int) -> int`: si `total == 0` → `1`; si `total > 0` → `ceil(total / size)`.
- Dependencia `get_paginacion(page: int = 1, size: int = 20)` que valida `page` ≥ 1 y `size` 1–100 y devuelve `(offset, limit, page, size)`; si `total > 0` y `page > pages` → `HTTPException(422, detail="Página fuera de rango")` (mensaje propio, sin texto de la base).

### D-02 — DTOs por módulo con `ConfigDict(extra="forbid")`

Cada `schemas.py` de módulo define `Create`, `Update` y `Read` (salvo `ventas` que solo tiene `Create` y `Read` por ahora, sin PATCH).

| Módulo | DTOs de entrada (`extra="forbid"`) | DTOs de salida |
|---|---|---|
| `editoriales` | `EditorialCreate` (`nombre`, `pais`); `EditorialUpdate` (`nombre?`, `pais?`) | `EditorialRead` (`id`, `nombre`, `pais`) |
| `generos` | `GeneroCreate` (`nombre`); `GeneroUpdate` (`nombre?`) | `GeneroRead` (`id`, `nombre`) |
| `autores` | `AutorCreate` (`nombre`, `nacionalidad`); `AutorUpdate` (`nombre?`, `nacionalidad?`) | `AutorRead` (`id`, `nombre`, `nacionalidad`) |
| `libros` | `LibroCreate` (`isbn`, `titulo`, `precio`, `stock_inicial`, `editorial_id`, `genero_id?`); `LibroUpdate` (`isbn?`, `titulo?`, `precio?`, `editorial_id?`, `genero_id?` — **sin** `stock`); `ReponerStockRequest` (`cantidad`) | `LibroRead` (`id`, `isbn`, `titulo`, `precio`, `stock`, `borrado_en?`, `editorial_id`, `genero_id?`) |
| `clientes` | `ClienteCreate` (`nombre`, `email`, `usuario_id?`); `ClienteUpdate` (`nombre?`, `email?`, `usuario_id?`) | `ClienteRead` (`id`, `nombre`, `email`, `usuario_id?`) |
| `clientes` (perfil) | `PerfilClienteCreate` (`telefono`, `direccion`, `cliente_id`) | `PerfilClienteRead` (`id`, `telefono`, `direccion`, `cliente_id`) |
| `usuarios` (salida) | — | `UsuarioRead` (**sin** `password_hash`) |
| `ventas` | `VentaCreate` (`cliente_id`, `renglones[{libro_id, cantidad}]` — **sin** precios ni totales) | `VentaRead` (`id`, `cliente_id`, `fecha`, `total`, `renglones[...]`) |

- Todos los campos de texto con `max_length` acorde a `VARCHAR(n)` de C-02 (segunda capa; la base es la primera).
- `UsuarioRead` excluye `password_hash` (se usa `model_config = ConfigDict(extra="forbid")` solo en entrada; en salida se omite el campo o se usa `Field(exclude=True)`).
- `LibroUpdate` sin `stock`: el stock solo se modifica vía `POST /libros/{id}/reponer-stock` (`ReponerStockRequest`), definido en C-04 como endpoint pero su lógica de descuento/reposición de stock queda para C-05 (SU-01: el stock no se descuenta en ventas todavía).

### D-03 — Endpoints por recurso

Router por módulo con `APIRouter(prefix="/<modulo>", tags=["<modulo>"])`:

- `POST /` → 201 (devuelve el `Read` creado; para ventas, `VentaRead` con totales calculados por el service en C-05).
- `GET /` → lista paginada `PaginatedResponse[Read]` con `page`/`size` de `get_paginacion`.
- `GET /{id}` → `Read` o 404 (`{"detail": "<recurso> no encontrado"}`).
- `PATCH /{id}` → `Read` actualizado con `exclude_unset`; **ventas no tiene PATCH**.
- `DELETE /libros/{id}` → 204 (soft delete: establece `borrado_en`, no borra físicamente).

Los servicios reciben `SessionDep` y usan `UnitOfWork` para commit/rollback (C-04 solo abre la sesión; C-05 define las transacciones con `UnitOfWork`).

### D-04 — Repositorios específicos

- `app/modules/libros/repository.py`: `LibroRepository(SoftDeleteRepository[Libro])` — hereda `get_by_id`/`get_all`/`count` que filtran `borrado_en IS NULL`, y `soft_delete` que establece `borrado_en`.
- `app/modules/ventas/repository.py`: `VentaRepository(BaseRepository[Venta])` con un método `get_con_detalle(id)` que usa `joinedload` (cliente, uno a uno) y `selectinload` (renglones → libro) para evitar N+1.

### D-05 — Handler global de `IntegrityError`

En `app/main.py` (o `app/core/errors.py`), un exception handler `@app.exception_handler(IntegrityError)` que:
- Captura `sqlalchemy.exc.IntegrityError`.
- Devuelve `JSONResponse(status_code=409, content={"detail": "Conflicto de integridad: registro duplicado o referencia inválida"})` (mensaje propio, **sin** el mensaje del driver ni el nombre de la restricción).
- También captura `DataError` (texto demasiado largo) → 422 con mensaje propio (red de seguridad, decidido en C-02 D-08).

### D-06 — Registro de routers en `main.py`

`app.include_router(...)` para los 6 routers de dominio (`editoriales`, `generos`, `autores`, `libros`, `clientes`, `ventas`) además de `health`.

### D-07 — Verificación: archivos `.http` en `test/`

La consigna exige `test/*.http` con respuesta esperada comentada. En C-04 se crean:
- `test/editoriales.http`, `test/generos.http`, `test/autores.http`, `test/libros.http`, `test/clientes.http`, `test/ventas.http`
Cada uno con: `POST` (201), `GET` lista paginada (200), `GET {id}` existente (200) e inexistente (404), `PATCH {id}` (200; ventas sin PATCH), `DELETE /libros/{id}` (204), caso de duplicado (409), caso de paginación fuera de rango (422).

## Risks / Trade-offs

- [`LibroUpdate` sin `stock` obliga a un endpoint separado `POST /libros/{id}/reponer-stock`] → aceptado; es lo que pide la consigna y separa responsabilidades.
- [El handler global de `IntegrityError` oculta el nombre de la restricción] → intencional (RN-12); el cliente recibe un mensaje genérico de conflicto.
- [`extra="forbid"` rechaza campos inesperados en la entrada] → es el comportamiento buscado (contrato estricto); los clientes deben enviar solo los campos del DTO.

## Migration Plan

No aplica a la base (el esquema ya existe vía Alembic en C-03). Rollback: revertir el commit; los `schemas.py`/`service.py`/`router.py` vuelven a docstring/esqueleto y se borra `app/core/paginacion.py`.

## Open Questions

- Ninguna que bloquee.
