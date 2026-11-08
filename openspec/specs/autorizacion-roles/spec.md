# autorizacion-roles Specification

## Purpose

Define cómo se decide si un usuario autenticado puede usar una ruta: con los roles vigentes leídos de la base en cada petición, respondiendo 403 cuando no tiene permiso y 401 cuando no hay sesión.

## Requirements

### Requirement: Permiso decidido con los roles vigentes de la base
Toda ruta que exija uno o más roles SHALL consultar, en cada petición, los roles vigentes del usuario en `asignacion_rol` (sin `revocada_en` y con `vence_en` nulo o futuro) y permitir el paso solo si alguno de ellos está entre los exigidos (RN-04). Los roles que trae el token NO SHALL intervenir en la decisión.

#### Scenario: Rol vigente permitido
- **WHEN** un usuario con rol vigente `ADMIN` envía `POST /editoriales/` con un cuerpo válido
- **THEN** la respuesta es 201

#### Scenario: Rol no permitido
- **WHEN** un usuario con rol vigente `VENDEDOR` (y ningún otro) envía `POST /libros/` con un cuerpo válido
- **THEN** la respuesta es 403 con `{"detail": "No tenés permiso para esta operación"}` y no se crea ningún libro

#### Scenario: Cliente en una ruta de personal
- **WHEN** un usuario con solo el rol `CLIENTE` envía `POST /ventas/`
- **THEN** la respuesta es 403

#### Scenario: Rol vencido
- **WHEN** la única asignación `ADMIN` de un usuario está abierta pero su `vence_en` ya pasó, y envía `POST /editoriales/`
- **THEN** la respuesta es 403

### Requirement: Revocación efectiva sobre una sesión abierta
Revocar un rol SHALL quitar el permiso en la petición siguiente del usuario afectado, con la misma cookie y sin esperar a que el token venza; `GET /auth/yo` SHALL mostrar la diferencia entre `roles_vigentes` y `roles_token`.

#### Scenario: Vendedor revocado con la sesión abierta
- **WHEN** un vendedor inicia sesión, crea una venta con éxito, un administrador le revoca `VENDEDOR` y el vendedor envía otra vez `POST /ventas/` con la misma cookie
- **THEN** la segunda venta responde 403
- **AND** `GET /auth/yo` con esa cookie responde 200 con `"roles_vigentes": []` y `"roles_token": ["VENDEDOR"]`

#### Scenario: Rol asignado después del login
- **WHEN** un usuario sin `ADMIN` inicia sesión, un administrador le asigna `ADMIN` y el usuario envía `POST /editoriales/` con la misma cookie
- **THEN** la respuesta es 201 aunque su token no traiga `ADMIN`

### Requirement: 401 antes que 403
Una ruta que exige rol SHALL responder 401 (y no 403) cuando falta la sesión o no es válida, y 403 solo cuando el usuario está identificado y activo pero no tiene un rol permitido.

#### Scenario: Sin cookie en una ruta de administrador
- **WHEN** se envía `POST /editoriales/` sin cookie
- **THEN** la respuesta es 401 con `{"detail": "No hay una sesión válida"}`

#### Scenario: Token alterado en una ruta de personal
- **WHEN** se envía `POST /ventas/` con una cookie cuyo token tiene un carácter de la firma cambiado
- **THEN** la respuesta es 401

#### Scenario: Usuario desactivado con rol vigente
- **WHEN** un administrador con sesión abierta queda con `activo = false` y envía `POST /editoriales/`
- **THEN** la respuesta es 401

### Requirement: Una sola conexión por petición autorizada
La identificación del usuario, la consulta de sus roles vigentes y las operaciones del Unit of Work de la ruta SHALL usar la misma sesión y la misma conexión de la base durante la petición.

#### Scenario: Petición autorizada con una conexión
- **WHEN** con el registro de consultas activo un administrador envía `POST /editoriales/`
- **THEN** la lectura del usuario, la de sus roles vigentes y el `INSERT` de la editorial se ejecutan en una única conexión tomada del pool
