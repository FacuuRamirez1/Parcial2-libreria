# Spec Delta

## Purpose

Actualiza el repositorio de libros para el Parcial: pasa a borrado lógico (filtra los dados de baja), agrega el acceso por id incluyendo dados de baja y el historial de movimientos.

## REMOVED Requirements

### Requirement: Ausencia de borrado lógico de libro en esta fase
**Reason**: desde C-10 existe `libro.borrado_en`; C-13 la usa para la baja lógica.
**Migration**: el repositorio pasa a `SoftDeleteRepository` y filtra los libros dados de baja (capacidad `baja-logica-libros`).

## MODIFIED Requirements

### Requirement: Escritura de libro mediante flush
El repositorio SHALL agregar, actualizar o eliminar (baja lógica) un libro con `flush()` y nunca con `commit()`. El stock NO SHALL editarse por PATCH ni por una escritura directa del repositorio: solo cambia por el punto único de escritura de stock.

#### Scenario: Alta de libro
- **WHEN** se invoca `add` con una entidad Libro y se hace flush
- **THEN** el libro persiste en la transacción abierta sin confirmarla

#### Scenario: Baja lógica
- **WHEN** se invoca `soft_delete` con un libro vigente
- **THEN** el libro queda con `borrado_en` no nulo y persiste sin confirmar

## ADDED Requirements

### Requirement: Lecturas del repositorio con baja lógica
`get_by_id`, `get_all`, `get_all_filtrado` y `count_filtrado` SHALL excluir los libros con `borrado_en` no nulo. El repositorio SHALL ofrecer `get_by_id_including_deleted` para lecturas internas que necesiten un libro dado de baja.

#### Scenario: Listado sin dados de baja
- **WHEN** se invoca `get_all_filtrado` después de dar de baja un libro
- **THEN** el libro dado de baja no aparece en el resultado

#### Scenario: Acceso incluyendo dados de baja
- **WHEN** se invoca `get_by_id_including_deleted` con el id de un libro dado de baja
- **THEN** devuelve la entidad

### Requirement: Historial de movimientos de un libro
El repositorio de libros SHALL ofrecer un método para listar los movimientos de un libro ordenados por id, sin carga perezosa, para `GET /libros/{id}/movimientos`.

#### Scenario: Movimientos ordenados
- **WHEN** se listan los movimientos de un libro con alta, reposición y venta
- **THEN** devuelve las tres filas ordenadas por id ascendente
