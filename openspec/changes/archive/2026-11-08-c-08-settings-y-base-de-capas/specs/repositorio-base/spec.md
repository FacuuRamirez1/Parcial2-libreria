# Spec Delta

## Purpose

Define el contrato genérico de acceso a datos por entidad: una sesión y la clase del modelo como entrada, operaciones de lectura y escritura que hacen flush sin confirmar, y soft delete por `borrado_en` para entidades con borrado lógico.

## ADDED Requirements

### Requirement: BaseRepository genérico por entidad
`BaseRepository[T]` SHALL recibir en su constructor la sesión de base de datos y la clase del modelo `T`, porque los genéricos se borran en tiempo de ejecución, y SHALL ofrecer al menos `get_by_id`, `get_all`, `count`, `add`, `update` y `delete`.

#### Instanciar un repositorio de libro
- **WHEN** se crea `BaseRepository(session, Libro)`
- **THEN** el repositorio opera sobre la tabla `libro` con la sesión dada

#### Operaciones de lectura y escritura
- **WHEN** se llaman `get_by_id`, `get_all`, `count`, `add`, `update` y `delete` sobre un `BaseRepository[T]`
- **THEN** cada una ejecuta la operación correspondiente sobre la entidad `T` usando la sesión del repositorio

### Requirement: Sin commit en el repositorio
`add` y `update` SHALL hacer `flush()` y NUNCA `commit()`: la confirmación y la reversión son responsabilidad exclusiva del `UnitOfWork`.

#### add no confirma
- **WHEN** se llama `repository.add(objeto)`
- **THEN** se ejecuta `flush()` pero no `commit()` en la sesión

#### update no confirma
- **WHEN** se llama `repository.update(objeto)`
- **THEN** se ejecuta `flush()` pero no `commit()` en la sesión

### Requirement: SoftDeleteRepository filtra dados de baja
`SoftDeleteRepository[T]` SHALL heredar de `BaseRepository[T]`, filtrar las filas con `borrado_en IS NULL` en `get_by_id`, `get_all` y `count`, y agregar `get_by_id_including_deleted` (ignora el filtro) y `soft_delete` (establece `borrado_en`).

#### get_all excluye dados de baja
- **WHEN** se llama `get_all()` sobre un `SoftDeleteRepository` de una entidad con filas dadas de baja
- **THEN** no devuelve las filas con `borrado_en` distinto de nulo

#### soft_delete establece borrado_en
- **WHEN** se llama `repository.soft_delete(objeto)`
- **THEN** `objeto.borrado_en` queda establecido y el objeto deja de aparecer en las consultas filtradas

### Requirement: Precarga declarada dentro del método
Cada repositorio de entidad SHALL declarar la carga anticipada (`joinedload` para relaciones a uno, `selectinload` para colecciones) dentro del método de lectura que la necesite, sin carga perezosa.

#### Lectura con carga anticipada
- **WHEN** se lee una entidad que tiene relaciones
- **THEN** la consulta incluye `joinedload` o `selectinload` para esas relaciones en la misma consulta
