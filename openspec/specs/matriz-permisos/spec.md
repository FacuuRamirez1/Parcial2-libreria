# matriz-permisos Specification

## Purpose

Fija qué exige cada ruta de la API: abierta para cualquiera, solo autenticada, personal (VENDEDOR o ADMIN) o solo ADMIN, según la tabla de endpoints de la consigna del parcial y las rutas del TP que se conservan.

## Requirements

### Requirement: Catálogo de lectura abierto
`GET /libros/`, `GET /libros/{id}`, `GET /editoriales/`, `GET /generos/`, `GET /editoriales/{id}/libros`, `GET /generos/{id}/libros` y `GET /autores/{id}/libros` SHALL pertenecer al grupo abierto y responder sin sesión. Las lecturas del TP de la misma familia que la tabla no lista (`GET /editoriales/{id}`, `GET /generos/{id}`, `GET /autores/`, `GET /autores/{id}`) SHALL ser también abiertas.

#### Scenario: Libros de una editorial sin sesión
- **WHEN** se envía `GET /editoriales/1/libros` sin cookie
- **THEN** la respuesta es 200 (o 404 si la editorial no existe), nunca 401

#### Scenario: Detalle de un autor sin sesión
- **WHEN** se envía `GET /autores/1` sin cookie
- **THEN** la respuesta es 200

### Requirement: Escrituras del catálogo solo para ADMIN
`POST /editoriales/`, `POST /generos/`, `POST /autores/`, `POST /libros/`, `PATCH /editoriales/{id}`, `PATCH /generos/{id}`, `PATCH /autores/{id}` y `PATCH /libros/{id}` SHALL pertenecer al grupo protegido y exigir el rol vigente `ADMIN`.

#### Scenario: Vendedor que crea un libro
- **WHEN** un vendedor con sesión envía `POST /libros/` con un cuerpo válido
- **THEN** la respuesta es 403 y no se crea ningún libro (caso C-06 de la consigna)

#### Scenario: Administrador que edita un autor
- **WHEN** un administrador con sesión envía `PATCH /autores/1` con un cuerpo válido
- **THEN** la respuesta es 200

### Requirement: Clientes y ventas para el personal
`POST /clientes/`, `GET /clientes/`, `GET /clientes/{id}`, `PATCH /clientes/{id}`, `POST /clientes/{id}/perfil`, `GET /clientes/{id}/ventas` y `POST /ventas/` SHALL pertenecer al grupo protegido y exigir un rol vigente `VENDEDOR` o `ADMIN`. `GET /ventas/` (listado) SHALL pertenecer al grupo protegido y exigir el rol vigente `ADMIN` (decisión del usuario, S-02).

#### Scenario: Vendedor registra una venta
- **WHEN** un vendedor con sesión envía `POST /ventas/` con un cuerpo válido
- **THEN** la respuesta es 201

#### Scenario: Cliente que lista clientes
- **WHEN** un usuario con solo el rol `CLIENTE` envía `GET /clientes/1`
- **THEN** la respuesta es 403

#### Scenario: Administrador lista ventas
- **WHEN** un administrador con sesión envía `GET /ventas/?page=1&size=20`
- **THEN** la respuesta es 200 con el envoltorio del listado

#### Scenario: Vendedor lista ventas
- **WHEN** un vendedor con sesión envía `GET /ventas/?page=1&size=20`
- **THEN** la respuesta es 403 (el listado es solo ADMIN, a diferencia de `GET /ventas/{id}`)

#### Scenario: Listado de ventas sin sesión
- **WHEN** se envía `GET /ventas/?page=1&size=20` sin cookie
- **THEN** la respuesta es 401

### Requirement: Administración de personal y seguridad solo para ADMIN
`POST /usuarios`, `GET /usuarios/{id}/roles`, `POST /usuarios/{id}/roles`, `DELETE /usuarios/{id}/roles/{rol}` y `GET /eventos` SHALL pertenecer al grupo protegido y exigir el rol vigente `ADMIN`.

#### Scenario: Vendedor que intenta asignarse un rol
- **WHEN** un vendedor con sesión envía `POST /usuarios/{su id}/roles` con `{"rol": "ADMIN"}`
- **THEN** la respuesta es 403 y no se crea ninguna asignación

#### Scenario: Historial sin sesión
- **WHEN** se envía `GET /eventos` sin cookie
- **THEN** la respuesta es 401

### Requirement: Detalle de venta protegido sin decisión de dueño todavía
`GET /ventas/{id}` (distinto del listado `GET /ventas/`, que es solo ADMIN) SHALL pertenecer al grupo protegido. Hasta que la decisión "personal o cliente dueño" se tome en el servicio de ventas, la ruta SHALL exigir un rol vigente `VENDEDOR` o `ADMIN`, de modo que ningún cliente vea ventas ajenas.

#### Scenario: Detalle sin sesión
- **WHEN** se envía `GET /ventas/1` sin cookie
- **THEN** la respuesta es 401

#### Scenario: Cliente pide un detalle de venta
- **WHEN** un usuario con solo el rol `CLIENTE` envía `GET /ventas/1`
- **THEN** la respuesta es 403

#### Scenario: Vendedor pide un detalle de venta
- **WHEN** un vendedor con sesión envía `GET /ventas/1`
- **THEN** la respuesta es 200 con el detalle

### Requirement: Sin rutas fuera de la matriz
La API NO SHALL exponer rutas distintas de las de esta matriz, de `/health/*` y de `/auth/*`; las rutas que la matriz no menciona y que otros changes agreguen SHALL declararse en esta capacidad al agregarse.

#### Scenario: Ruta no declarada
- **WHEN** se envía `DELETE /usuarios/1` con una sesión de administrador
- **THEN** la respuesta es 405 (o 404), nunca 2xx

### Requirement: Escenarios de otras capacidades presuponen el permiso
Los escenarios de otras capacidades que envían peticiones a rutas del grupo protegido SHALL entenderse enviados con una sesión válida de un usuario sin cambio de contraseña pendiente y con un rol que esta matriz permite para esa ruta; sin esa sesión, la respuesta es la que fija esta capacidad (401 o 403).

#### Scenario: Alta de editorial de endpoints-crud
- **WHEN** un administrador con sesión envía `POST /editoriales/` con un cuerpo válido, como en el escenario "Alta de editorial"
- **THEN** la respuesta es 201 con el `EditorialRead` creado
- **AND** la misma petición sin cookie responde 401
