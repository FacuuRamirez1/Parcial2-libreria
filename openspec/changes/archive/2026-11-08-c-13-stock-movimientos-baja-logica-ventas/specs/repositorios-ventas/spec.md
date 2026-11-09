# Spec Delta

## Purpose

Actualiza el repositorio de ventas para que el detalle siga precargando el libro de cada renglón aunque el libro esté dado de baja, con el mismo número fijo de consultas.

## MODIFIED Requirements

### Requirement: Detalle de venta con precarga de relaciones
El repositorio SHALL devolver una venta con su cliente, sus renglones y el libro de cada renglón precargados en un número fijo de consultas, independiente de la cantidad de renglones y **aunque el libro esté dado de baja** (no aplica filtro de `borrado_en` sobre la relación `renglon_venta → libro`).

#### Scenario: Detalle de venta sin N+1
- **WHEN** se invoca `get_con_detalle` con un id de venta
- **THEN** devuelve la venta con cliente (`joinedload`) y renglones con libro (`selectinload`) ya cargados, sin consultas adicionales por renglón

#### Scenario: Detalle con libro dado de baja
- **WHEN** se invoca `get_con_detalle` de una venta cuyo libro fue dado de baja
- **THEN** el libro se carga igual y su título está disponible sin consultas adicionales
