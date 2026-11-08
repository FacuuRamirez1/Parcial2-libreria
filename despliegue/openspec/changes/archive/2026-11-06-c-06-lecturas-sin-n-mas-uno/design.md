# Design: C-06 — Lecturas sin N+1

## Contexto

`Libro` tiene relaciones `editorial` (a uno), `genero` (a uno, nullable) y `autorias` (colección de `LibroAutor`, cada una con `autor`). Todas usan `lazy="raise"`, por lo que leerlas sin precarga lanza `InvalidRequestError`. `Venta` ya precarga `cliente` y `renglones → libro` en `VentaRepository.get_con_detalle` y en el listado.

## Decisiones

### D-01 — DTO de detalle aditivo

`LibroDetalleRead` extiende `LibroRead` y agrega:

- `editorial: EditorialRead`
- `genero: GeneroRead | None`
- `autores: list[LibroAutorRead]` con `autor: AutorRead`, `rol` y `orden`

Se mantiene `LibroRead` plano para `POST /libros/` y `PATCH /libros/{id}`; así no se fuerza una recarga extra en escrituras. `GET /libros/{id}` y `GET /libros/` usan el DTO de detalle.

### D-02 — Precarga en el repositorio

`LibroRepository` expone `_opciones_detalle()` con:

- `joinedload(Libro.editorial)`
- `joinedload(Libro.genero)`
- `selectinload(Libro.autorias).joinedload(LibroAutor.autor)`

`get_all_filtrado` aplica esas opciones siempre; `get_by_id_con_detalle(id)` las aplica a la búsqueda por id con filtro `borrado_en IS NULL`. No se usa carga perezosa en ningún punto.

### D-03 — Mapeo explícito a DTO

El service construye `LibroDetalleRead` con un helper `_a_detalle(libro)`, leyendo `libro.editorial`, `libro.genero` y `libro.autorias` ya precargados. No se usa `model_dump()` sobre el modelo para evitar disparar relaciones no cargadas.

### D-04 — Ventas: sin cambios de código, con evidencia

`VentaRepository.get_con_detalle` ya usa `joinedload(cliente)` + `selectinload(renglones).joinedload(libro)`. C-06 agrega tests que prueban que el conteo de SELECT es fijo con 1 vs. 3 renglones.

### D-05 — Medición del conteo

Los tests registran un listener `before_cursor_execute` en `engine.sync_engine`, cuentan solo sentencias `SELECT` y lo quitan en `finally`. Se comparan dos escenarios (1 vs. 3 hijos) y se exige el mismo número; además se fija el presupuesto: 2 SELECT para detalle de libro/venta y 3 para el listado de libros (count + página + selectin).

### D-06 — Presupuesto de consultas

| Lectura | Consultas esperadas | Independencia |
|---|---|---|
| `GET /libros/{id}` | 2 | 0/1/N autores |
| `GET /libros/` | 3 | 0/1/N libros y autores |
| `GET /ventas/{id}` | 2 | 1/N renglones |

## Riesgos y mitigaciones

- **Respuesta más pesada en listados**: se acepta por el requisito de detalle precargado; la paginación limita a 100 ítems.
- **Duplicación de filas por `joinedload` en colecciones**: se usa `selectinload` para colecciones, nunca `joinedload`, evitando el producto cartesiano.
- **Regresión de contrato**: los campos existentes se conservan; solo se agregan anidados.
