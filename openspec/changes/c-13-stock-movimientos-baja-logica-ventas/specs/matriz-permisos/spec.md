# Spec Delta

## Purpose

Declara en la matriz de permisos las rutas nuevas de stock y baja de libros, y reemplaza la restricción provisoria del detalle de venta por la decisión de dueño o personal.

## REMOVED Requirements

### Requirement: Detalle de venta protegido sin decisión de dueño todavía
**Reason**: C-13 implementa la decisión de dueño en el servicio de ventas.
**Migration**: ver la capacidad `ventas-propias`; la ruta deja de exigir `requiere_rol` y el servicio responde 403 si el usuario no es personal ni dueño.

## ADDED Requirements

### Requirement: Stock y baja de libros solo para ADMIN
`DELETE /libros/{id}`, `POST /libros/{id}/reponer` y `GET /libros/{id}/movimientos` SHALL pertenecer al grupo protegido y exigir el rol vigente `ADMIN`.

#### Scenario: Vendedor que repone
- **WHEN** un vendedor con sesión envía `POST /libros/1/reponer`
- **THEN** la respuesta es 403 y el stock no cambia

#### Scenario: Administrador que da de baja
- **WHEN** un administrador con sesión envía `DELETE /libros/1`
- **THEN** la respuesta es 204

#### Scenario: Vendedor que pide movimientos
- **WHEN** un vendedor con sesión envía `GET /libros/1/movimientos`
- **THEN** la respuesta es 403

### Requirement: Mis ventas y detalle de venta autenticados
`GET /mis-ventas` y `GET /ventas/{id}` SHALL pertenecer al grupo protegido y exigir solo autenticación (sin rol). `GET /ventas/` (listado) SHALL seguir exigiendo `ADMIN`.

#### Scenario: Cliente en mis-ventas
- **WHEN** un cliente autenticado envía `GET /mis-ventas`
- **THEN** la respuesta es 200 con sus ventas

#### Scenario: Cliente en el detalle de una venta ajena
- **WHEN** un cliente autenticado envía `GET /ventas/{id}` de una venta que no es suya
- **THEN** la respuesta es 403

#### Scenario: Listado de ventas como cliente
- **WHEN** un cliente autenticado envía `GET /ventas/`
- **THEN** la respuesta es 403

#### Scenario: Sin sesión
- **WHEN** se envía `GET /mis-ventas` o `GET /ventas/{id}` sin cookie
- **THEN** la respuesta es 401
