# Spec Delta

## Purpose

Define los repositorios específicos por módulo: `LibroRepository` hereda de `SoftDeleteRepository` (usa `borrado_en`); `VentaRepository` precarga relaciones para evitar N+1.

## ADDED Requirements

### Requirement: LibroRepository hereda de SoftDeleteRepository
`app/modules/libros/repository.py` define `LibroRepository(SoftDeleteRepository[Libro])`. Hereda `get_by_id`, `get_all`, `count` que filtran `borrado_en IS NULL`, y `soft_delete` que establece `borrado_en = datetime.now(UTC)`.

#### Scenario: Soft delete de libro
- **WHEN** se llama `LibroRepository.soft_delete(libro)`
- **THEN** `libro.borrado_en` se establece y las consultas posteriores (`get_by_id`, `get_all`) no devuelven ese libro

### Requirement: VentaRepository con precarga de relaciones
`app/modules/ventas/repository.py` define `VentaRepository(BaseRepository[Venta])` con un método `get_con_detalle(id)` que usa `joinedload` (cliente, relación a uno) y `selectinload` (renglones → libro, colección) en la misma consulta para evitar N+1.

#### Scenario: Carga anticipada en VentaRepository
- **WHEN** se ejecuta `VentaRepository.get_con_detalle(id)`
- **THEN** la consulta incluye `joinedload` para `venta.cliente` y `selectinload` para `venta.renglones` (con `libro` dentro de cada renglón)
