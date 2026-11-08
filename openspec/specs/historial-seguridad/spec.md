# historial-seguridad Specification

## Purpose

Define qué operaciones de seguridad dejan una línea en `evento_seguridad`, con qué actor y en qué transacción, y cómo el administrador consulta ese historial.

## Requirements

### Requirement: Evento en la misma transacción que el cambio de rol
Cada asignación y cada revocación de rol exitosa SHALL agregar una fila en `evento_seguridad` con `actor` = correo del administrador y una `accion` que nombre la operación, el rol y el usuario afectado, en la misma transacción que la escritura en `asignacion_rol` (RN-16). Una operación rechazada (403, 404, 409 o 422) NO SHALL dejar evento.

#### Scenario: Asignación con su evento
- **WHEN** un administrador asigna `VENDEDOR` a un usuario
- **THEN** existe un `evento_seguridad` nuevo con su correo como `actor` y una `accion` que menciona la asignación de `VENDEDOR` a ese usuario

#### Scenario: Revocación con su evento
- **WHEN** un administrador revoca `VENDEDOR` a un usuario
- **THEN** existe un `evento_seguridad` nuevo con su correo como `actor` y una `accion` que menciona la revocación

#### Scenario: Autoprotección sin evento
- **WHEN** un administrador intenta revocarse su propio `ADMIN` y recibe 409
- **THEN** la cantidad de filas de `evento_seguridad` no cambia

#### Scenario: Falla al escribir el evento de una revocación
- **WHEN** la escritura de `revocada_en` se hace pero la inserción del evento es rechazada por la base
- **THEN** la asignación sigue abierta

### Requirement: Listado paginado del historial
`GET /eventos` SHALL devolver 200 con el envoltorio `{items, total, page, size, pages}` de los eventos, del más reciente al más antiguo, cada uno con `id`, `cuando`, `actor` y `accion`; `page` ≥ 1, `size` de 1 a 100 (20 por defecto), y una página inexistente o un parámetro fuera de rango SHALL responder 422.

#### Scenario: Primer evento es el más reciente
- **WHEN** un administrador revoca un rol y luego pide `GET /eventos?page=1&size=5`
- **THEN** el primer elemento de `items` es el evento de esa revocación

#### Scenario: Página fuera de rango
- **WHEN** hay 3 eventos y un administrador pide `GET /eventos?page=2&size=5`
- **THEN** la respuesta es 422

#### Scenario: Tamaño fuera de rango
- **WHEN** un administrador pide `GET /eventos?size=500`
- **THEN** la respuesta es 422

#### Scenario: Vendedor que pide el historial
- **WHEN** un vendedor con sesión pide `GET /eventos`
- **THEN** la respuesta es 403

### Requirement: Actor de texto en el historial
El `actor` de cada evento SHALL ser texto (el correo de quien hizo la operación, o `SISTEMA` para la carga de los datos iniciales) y no una referencia a un usuario, de modo que el historial sobreviva a cambios en `usuario`.

#### Scenario: Evento del sistema listado
- **WHEN** existe un evento con `actor = 'SISTEMA'` y un administrador pide `GET /eventos`
- **THEN** ese evento aparece con `"actor": "SISTEMA"`
