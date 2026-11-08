# Spec Delta

## Purpose

Actualiza las lecturas del catálogo para que excluyan los libros dados de baja sin perder la precarga ni el número fijo de consultas.

## ADDED Requirements

### Requirement: El catálogo excluye los libros dados de baja
`GET /libros/` y `GET /libros/{id}` SHALL excluir los libros con `borrado_en` no nulo, manteniendo la precarga de editorial, género y autores y el número fijo de consultas. `total` SHALL contar solo los libros vigentes con los filtros aplicados.

#### Scenario: Listado sin dados de baja
- **WHEN** se consulta `GET /libros/` después de dar de baja un libro
- **THEN** el libro no aparece en `items` ni se cuenta en `total`

#### Scenario: Detalle de un libro dado de baja
- **WHEN** se consulta `GET /libros/{id}` de un libro dado de baja
- **THEN** la respuesta es 404
