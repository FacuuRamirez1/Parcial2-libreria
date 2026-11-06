# repositorios-modulo Specification

## Purpose
Define los repositorios específicos por módulo: `LibroRepository` hereda de `SoftDeleteRepository` (usa `borrado_en`) y agrega búsqueda filtrada; `VentaRepository` precarga relaciones para evitar N+1.

## Requirements

### Requirement: LibroRepository hereda de SoftDeleteRepository

`app/modules/libros/repository.py` SHALL definir `LibroRepository(SoftDeleteRepository[Libro])` y heredar `get_by_id`, `get_all`, `count` (que filtran `borrado_en IS NULL`) y `soft_delete` (que establece `borrado_en = datetime.now(UTC)`).

#### Scenario: Soft delete de libro

- **WHEN** se llama `LibroRepository.soft_delete(libro)`
- **THEN** `libro.borrado_en` queda establecido y las consultas posteriores (`get_by_id`, `get_all`) no devuelven ese libro

### Requirement: LibroRepository con búsqueda filtrada

`LibroRepository` SHALL exponer `get_all_filtrado` y `count_filtrado`, que aceptan `titulo` y `genero_id` opcionales, respetan el filtro de soft delete y aplican paginación (`offset`/`limit`). El patrón de `titulo` MUST usar `ilike` con parámetro ligado.

#### Scenario: Búsqueda combinada

- **WHEN** se llama `get_all_filtrado(titulo="cien", genero_id=2, offset=0, limit=20)`
- **THEN** la consulta filtra por `borrado_en IS NULL`, `titulo ILIKE '%cien%'` y `genero_id = 2`, con el patrón como parámetro ligado

#### Scenario: Conteo coherente con el listado

- **WHEN** se llama `count_filtrado` con los mismos filtros que `get_all_filtrado`
- **THEN** el total devuelto coincide con la cantidad de filas que cumplen esos filtros

### Requirement: VentaRepository con precarga de relaciones

`app/modules/ventas/repository.py` SHALL definir `VentaRepository(BaseRepository[Venta])` con un método `get_con_detalle(id)` que usa `joinedload` (cliente, relación a uno) y `selectinload` (renglones, colección) en la misma consulta para evitar N+1.

#### Scenario: Carga anticipada en VentaRepository

- **WHEN** se ejecuta `VentaRepository.get_con_detalle(id)`
- **THEN** la consulta incluye `joinedload` para `venta.cliente` y `selectinload` para `venta.renglones` con `joinedload` de `renglon.libro`
