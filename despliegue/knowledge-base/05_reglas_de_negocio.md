# Reglas de Negocio

Los códigos `RN-NN` coinciden con los de la consigna, que los cita por número (por ejemplo "RN-04 a RN-07"). Los requisitos no funcionales usan `NF-NN`.

## Dominio: Catálogo

- **RN-01**: el ISBN de un libro es único. Garante: UNIQUE en la base; la violación responde 409.
- **RN-03**: el precio de un libro es mayor que cero y el stock nunca es negativo. Garante: CHECK en la base y validación del DTO (422 desde el DTO).
- **RN-11**: el listado de libros se puede filtrar por parte del título, sin distinguir mayúsculas. Garante: restricciones en `Query`; parámetro ligado, nunca SQL armado con texto (`ilike` con parámetro).

## Dominio: Clientes

- **RN-02**: el email de un cliente es único. Garante: UNIQUE en la base; 409.
- **RN-09**: un cliente tiene como máximo un perfil. Garante: UNIQUE en `perfil_cliente.cliente_id`; 409.

## Dominio: Ventas

- **RN-04**: una venta se crea con sus renglones. Los datos de cada renglón viajan dentro del cuerpo del alta de la venta; no existe un alta de renglones por separado. Garante: DTO anidado; los renglones se agregan a `venta.renglones`.
- **RN-05**: una venta tiene al menos un renglón, y un mismo libro no aparece en dos renglones. Garante: validación del DTO; 422.
- **RN-06**: el precio de cada renglón se copia del libro al registrar la venta y no cambia aunque después cambie el precio del libro. Garante: el servidor lo lee de la base; nunca viaja en el DTO.
- **RN-07**: el total de la venta lo calcula el servidor como suma de `cantidad × precio_unitario`. Garante: no viaja en el DTO.
- **RN-08**: las ventas no se modifican; registran un hecho. Garante: no hay PATCH de ventas.

## Dominio: Listados y errores (transversales)

- **RN-10**: todo listado se pagina con `limit` (de 1 a 100, por defecto 20) y `offset` (desde 0). Garante: restricciones en `Query`; 422 si se violan.
- **RN-12**: ningún error devuelve al cliente texto interno de la base (nombres de tablas, restricciones o trazas). Garante: traducción del `IntegrityError` a un mensaje propio.

## Requisitos no funcionales

- **NF-01 Asincronía**: todos los handlers son `async def`; ninguna llamada bloqueante (`time.sleep`, `requests`, acceso síncrono a la base).
- **NF-02 Credenciales**: ninguna contraseña en el código, en `alembic.ini` ni en el repositorio.
- **NF-03 SQL**: nunca armado por concatenación de texto con datos del usuario.
- **NF-04 Carga perezosa prohibida**: toda relación que se lee se precarga en la consulta (`joinedload` para relaciones a uno, `selectinload` para colecciones).
- **NF-05 Errores**: mensajes propios; nunca el texto de la base ni una traza.
- **NF-06 Unicidad**: garantizada por la base; no se verifica con una consulta previa.
- **NF-07 Diagnóstico**: las consultas emitidas se pueden ver en consola (por ejemplo `echo=True` configurable).

## Excepciones globales

- Un proyecto que no levanta, que no crea su esquema con `alembic upgrade head` sobre una base vacía o que contiene credenciales reales en el repositorio **no se corrige** hasta que se subsane.
- En el alta de libro, ningún `if` consulta antes si un id existe: se escribe y, si la base rechaza la clave foránea, se responde 409.
