# Tasks

> Cada tarea indica cómo se verifica su completado. No ejecutar código de aplicación, migraciones, `requirements.txt`, `env.example` ni tests en esta fase (propose): las tareas se ejecutan en el apply tras aprobación del change.

## 1. Verificar capa base de `app/core` (contrato de C-08)

- [ ] 1.1 Verificar que `app/core/repository.py` expone `BaseRepository[T]` (constructor `(session, model)`, `get_by_id`, `get_all(offset, limit)`, `count`, `add`, `update`, `delete` con `flush()` sin `commit()`) y `SoftDeleteRepository[T]` (filtra `borrado_en IS NULL`, `get_by_id_including_deleted`, `soft_delete`); verificar con `grep`/import estático que las firmas coinciden con el design (D-02).
- [ ] 1.2 Verificar que `app/core/unit_of_work.py` expone `UnitOfWork` gestor de contexto async: confirma al salir, revierte ante excepción, no crea ni cierra la sesión (D-04).
- [ ] 1.3 Verificar/documentar el contrato de `app/core/paginacion.py`: `get_paginacion(page=1, size=20)` devuelve `Paginacion(page, size)` con propiedades `limit`/`offset` de compatibilidad; página inexistente (`total > 0` y `page > pages`) → 422; `total == 0` → `pages = 1`, `items = []` (D-05). Si la implementación actual usa `limit/offset`, anotar el ajuste requerido sin ejecutarlo.

## 2. Crear `repository.py` por módulo (6 módulos)

- [ ] 2.1 `app/modules/editoriales/repository.py`: `EditorialRepository(BaseRepository[Editorial])` con métodos genéricos; escritura por `flush()` (spec `repositorios-editoriales`).
  - Verificación: import estático; `issubclass(EditorialRepository, BaseRepository)` es `True`.
- [ ] 2.2 `app/modules/generios/repository.py`: `GeneroRepository(BaseRepository[Genero])` con métodos genéricos y `flush()` (spec `repositorios-generios`).
  - Verificación: import estático; subclase de `BaseRepository`.
- [ ] 2.3 `app/modules/autores/repository.py`: `AutorRepository(BaseRepository[Autor])` con métodos genéricos y `flush()` (spec `repositorios-autores`).
  - Verificación: import estático; subclase de `BaseRepository`.
- [ ] 2.4 `app/modules/libros/repository.py`: `LibroRepository(BaseRepository[Libro])` con `get_all_filtrado(titulo, genero_id, offset, limit)` (`ILIKE` ligado), `count_filtrado(titulo, genero_id)`, precarga `joinedload(editorial)` + `joinedload(genero)` dentro de los métodos de listado/detalle; sin `soft_delete` ni filtro `borrado_en` (spec `repositorios-libros`, D-03).
  - Verificación: import estático; los métodos declaran `joinedload`/`selectinload`; no referencia `borrado_en`.
- [ ] 2.5 `app/modules/clientes/repository.py`: `ClienteRepository(BaseRepository[Cliente])` con `get_by_email(email)` y métodos genéricos (spec `repositorios-clientes`).
  - Verificación: import estático; existe `get_by_email`.
- [ ] 2.6 `app/modules/ventas/repository.py`: `VentaRepository(BaseRepository[Venta])` con `get_con_detalle(id)` (`joinedload(cliente)` + `selectinload(renglones).joinedload(libro)`), `get_all`/`count` con filtro opcional `cliente_id` (spec `repositorios-ventas`).
  - Verificación: import estático; `get_con_detalle` declara precargas fijas (2 consultas, sin N+1).

## 3. Crear `unit_of_work.py` por módulo (6 módulos)

- [ ] 3.1 `app/modules/editoriales/unit_of_work.py`: `EditorialesUnitOfWork(UnitOfWork)` que compone `EditorialRepository` sobre la misma sesión (spec `unit-of-work-modulos`).
  - Verificación: import estático; expone `repositorios.editoriales`.
- [ ] 3.2 `app/modules/generios/unit_of_work.py`: `GenerosUnitOfWork(UnitOfWork)` con `GeneroRepository`.
  - Verificación: import estático; expone `repositorios.generos`.
- [ ] 3.3 `app/modules/autores/unit_of_work.py`: `AutoresUnitOfWork(UnitOfWork)` con `AutorRepository`.
  - Verificación: import estático; expone `repositorios.autores`.
- [ ] 3.4 `app/modules/libros/unit_of_work.py`: `LibrosUnitOfWork(UnitOfWork)` con `LibroRepository`.
  - Verificación: import estático; expone `repositorios.libros`.
- [ ] 3.5 `app/modules/clientes/unit_of_work.py`: `ClientesUnitOfWork(UnitOfWork)` con `ClienteRepository`.
  - Verificación: import estático; expone `repositorios.clientes`.
- [ ] 3.6 `app/modules/ventas/unit_of_work.py`: `VentasUnitOfWork(UnitOfWork)` con `VentaRepository`.
  - Verificación: import estático; expone `repositorios.ventas`.

## 4. Refactor `service.py` de los 6 módulos a UnitOfWork

- [ ] 4.1 `app/modules/editoriales/service.py`: recibe `UnitOfWork`, lo abre con `async with`, usa `uow.repositorios.editoriales`, sin `session.commit()` ni construcción de UoW.
  - Verificación: no recibe `SessionDep`; no llama `session.commit()`; abre `async with uow:`.
- [ ] 4.2 `app/modules/generios/service.py`: idéntico patrón (spec `repositorios-generios`).
- [ ] 4.3 `app/modules/autores/service.py`: idéntico patrón (spec `repositorios-autores`).
- [ ] 4.4 `app/modules/libros/service.py`: recibe `UoW`, listado/detalle con paginación `{items,total,page,size,pages}` y página inexistente → 422; búsqueda filtrada por título/género (spec `repositorios-libros`, D-05).
  - Verificación: listado devuelve envoltorio paginado; `page > pages` con total>0 → 422.
- [ ] 4.5 `app/modules/clientes/service.py`: recibe `UoW` (spec `repositorios-clientes`).
- [ ] 4.6 `app/modules/ventas/service.py`: recibe `UoW`, detalle de venta con precarga fija; alta de venta con commit/rollback solo en el UoW (spec `repositorios-ventas`, D-04).
  - Verificación: detalle precarga cliente+renglones+libro sin N+1.

## 5. Refactor `router.py` de los 6 módulos a dependencia de UnitOfWork

- [ ] 5.1 `app/modules/editoriales/router.py`: dependencia que construye `EditorialesUnitOfWork(session)` desde `get_session` y se lo pasa al servicio sin abrir; conserva rutas incluidas `GET /editoriales/{id}/libros` (IN-04).
  - Verificación: router no abre el UoW; service lo abre con `async with`.
- [ ] 5.2 `app/modules/generios/router.py`: idéntico, conserva `GET /generos/{id}/libros`.
- [ ] 5.3 `app/modules/autores/router.py`: idéntico, conserva `GET /autores/{id}/libros`.
- [ ] 5.4 `app/modules/libros/router.py`: listado con envoltorio paginado; `page`/`size` validados (`page ≥ 1`, `size` 1–100 def. 20); página inexistente → 422.
- [ ] 5.5 `app/modules/clientes/router.py`: conserva rutas de perfil y ventas del cliente.
- [ ] 5.6 `app/modules/ventas/router.py`: sin PATCH; alta de venta con `BackgroundTasks` para aviso de comprobante solo si se confirma.

## 6. Pruebas `.http` (regresión + paginación)

- [ ] 6.1 Repetir todos los casos de `test/*.http` del TP contra el refactor (regresión de C-01..C-06), con respuesta esperada comentada (201/404/409/422, mensajes propios).
  - Verificación: ejecutar cada `.http` contra `uvicorn app.main:app` con `alembic upgrade head` aplicado; respuestas coinciden con el comentario esperado.
- [ ] 6.2 Agregar casos de paginación nueva: `page=0` → 422, `size=101` → 422, valores por defecto `page=1`/`size=20`, `total == 0` → `pages=1` `items=[]`, `page > pages` → 422 "Página fuera de rango".
  - Verificación: cada caso `.http` responde con el código y forma esperados.

## 7. Chequeo integral de reglas duras

- [ ] 7.1 Verificar que ningún servicio recibe `SessionDep` ni llama `session.commit()`; ningún repositorio hace `commit()`; el UoW no cierra la sesión (NF-10).
- [ ] 7.2 Verificar que no hay `create_all`, ni `float` para dinero, ni carga perezosa, ni SQL concatenado; todos los handlers `async def`.
- [ ] 7.3 Verificar `extra="forbid"` en DTOs de entrada, `exclude_unset` en PATCH, ninguna respuesta con `password_hash`.

## Workflow follow-up

- Archivar con `/opsx:archive c-09-modulos-a-repositorios-uow` y marcar `[x]` C-09 en `CHANGES.md`. No commitear sin orden explícita del usuario (DD-16).
