# Reglas de Negocio

> **Dos numeraciones conviven.** Las reglas **RN-01..RN-16 del Parcial (pendiente)** se numeran de nuevo y **reemplazan** a las del TP en lo que se superponen. Las del TP (implementado) se citan como **TP RN-NN** y solo siguen vigentes las que el Parcial dice (CHECK de precio y stock, búsqueda por título con parámetros ligados) o las que no contradice (perfil único). Los requisitos no funcionales usan `NF-NN`.

## Parcial (pendiente): RN-01 a RN-16

| Regla | Enunciado | Garante |
|---|---|---|
| **RN-01** | El correo de un usuario, el de un cliente, el nombre de una editorial y el de un género son únicos. El ISBN de un libro es único entre los que no están dados de baja. | UNIQUE e índice único parcial en la base; 409 con mensaje propio |
| **RN-02** | El auto-registro crea el usuario, su rol CLIENTE y su ficha de cliente: o quedan las tres filas, o ninguna. Si ya existe un cliente con ese correo, el registro da 409 y no se apropia de esa ficha. | Un solo Unit of Work |
| **RN-03** | Un usuario tiene a lo sumo una asignación abierta por rol. | Índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`; 409 |
| **RN-04** | Los permisos se deciden con los roles vigentes en la base, en cada petición. Los roles que trae el token son informativos. | Dependencia que consulta `asignacion_rol` |
| **RN-05** | Un administrador no puede revocarse su propio rol ADMIN, y el sistema nunca queda sin administradores vigentes. | Comprobación en el servicio; 409 |
| **RN-06** | Mientras un usuario tenga el cambio de contraseña pendiente, solo puede usar las rutas de `/auth` y las que no piden sesión. | Dos grupos de rutas; 403 |
| **RN-07** | Después de 5 intentos fallidos con el mismo correo desde la misma dirección en 60 segundos, el login responde 429 sin verificar la contraseña. Un login correcto reinicia la cuenta: los fallos anteriores siguen en la tabla pero dejan de contar. | Conteo sobre `intento_acceso`; `Retry-After` |
| **RN-08** | El login responde lo mismo, y tarda lo mismo, exista o no el correo. | Mismo mensaje; verificación contra un hash ficticio |
| **RN-09** | Una venta nace con sus renglones (al menos uno, sin libros repetidos), con el precio de cada renglón copiado del libro y el total calculado por el servidor. Las ventas no se modifican. | DTO; el precio y el total nunca viajan en el cuerpo; no hay PATCH |
| **RN-10** | Registrar una venta descuenta el stock de cada libro y deja un movimiento por renglón. Si un libro no alcanza, no queda ninguna de esas escrituras (ni venta, ni renglones, ni descuentos, ni movimientos). | Un solo Unit of Work; 409 |
| **RN-11** | El stock de un libro solo cambia a través de movimientos: el alta con stock inicial, la reposición y la venta. No se edita por PATCH. | Punto único de escritura de stock |
| **RN-12** | `movimiento_stock` es de solo agregado: nadie puede modificar ni borrar sus filas. | Disparador en la base, instalado por migración |
| **RN-13** | Un libro dado de baja deja de aparecer en el catálogo y no se puede vender ni reponer, pero sus datos se conservan y las ventas anteriores lo siguen mostrando. | Borrado lógico; 409 |
| **RN-14** | Lo propio solo pide estar autenticado: un cliente ve sus ventas y ninguna otra. | `/mis-ventas` y comprobación de dueño; 403 |
| **RN-15** | Ningún error devuelve al cliente texto interno de la base. Ninguna entrada inválida termina en un 500. | Traducción del `IntegrityError`; validación en el contrato |
| **RN-16** | Cada alta de personal, cambio de rol y cambio de contraseña deja una línea en `evento_seguridad`, en la misma transacción que el cambio. | Un solo Unit of Work |

> Nota de extracción: en el texto de la consigna las etiquetas RN y los enunciados vienen desalineados una fila; la numeración de arriba sigue el orden de los enunciados y se confirmó con las citas del texto (Ej. 5 cita RN-04 y RN-05; Ej. 6 cita RN-02, RN-10 y RN-16; Ej. 7 cita RN-07 y RN-08, RN-12; Ej. 2 cita RN-12 para el trigger; Ej. 3 cita RN-11 para `extra="forbid"`).

### Reglas adicionales del Parcial (de las consignas, sin código RN)
- **Reasignar un rol vencido** cierra la fila anterior y abre una nueva. El vencimiento llega con zona horaria y en el futuro: sin zona o ya pasado → 422 (no 409).
- **Contraseñas**: máximo 72 **bytes** (no caracteres) en todo campo que termina en bcrypt (registro, login, actual y nueva del cambio) → 422. Costo de bcrypt en la configuración. bcrypt siempre con `to_thread` y bajo un semáforo; el hash se calcula **antes** de abrir la transacción.
- **Orden del login**: 1) límite de intentos (una consulta; si se superó, 429 + `Retry-After` sin calcular hash); 2) verificación contra el hash del usuario o contra el hash ficticio si el correo no existe.
- **Cambio de contraseña**: no invalida sesiones abiertas ni emite token nuevo; `debe_cambiar_password` queda en falso y la misma cookie sirve.
- **Baja de libro**: 204; no se puede vender ni reponer un libro dado de baja (409); el ISBN puede volver a cargarse (201), y un segundo vigente con ese ISBN da 409.
- **Contratos**: los DTO de entrada usan `extra="forbid"` (nadie se registra con un rol ni edita el stock por PATCH); PATCH con `exclude_unset`; ninguna respuesta incluye `password_hash`.
- **Listados**: `page` ≥ 1, `size` 1–100 (def. 20), página inexistente → 422, `total` con los mismos filtros, cero resultados = una página vacía.
- **Aviso de comprobante**: `BackgroundTasks`, solo si la operación se confirmó, después de enviar la respuesta.
- **Intento de acceso**: cada login (correcto o fallido) se anota desde sesión y transacción propias, siempre confirmadas; un comentario en el código dice qué hace distinto, por qué no puede compartir la transacción y su costo (deja filas aunque la petición falle).
- **Invariante**: para cada libro, `stock` = suma de la `cantidad` de sus movimientos.

## TP caps 1-4 (implementado): reglas y su destino

| Regla del TP | Estado frente al Parcial |
|---|---|
| TP RN-01 ISBN único (UNIQUE, 409) | **Superada** por RN-01: único solo entre vigentes (índice parcial) |
| TP RN-02 email de cliente único | Vigente; incluida en RN-01 |
| TP RN-03 precio > 0, stock ≥ 0 (CHECK + DTO) | **Vigente** (la consigna lo confirma) |
| TP RN-04 venta nace con renglones | Vigente → RN-09 |
| TP RN-05 mínimo un renglón, sin libros repetidos (422) | Vigente → RN-09 |
| TP RN-06 precio copiado del libro | Vigente → RN-09 |
| TP RN-07 total calculado por el servidor | Vigente → RN-09 |
| TP RN-08 las ventas no se modifican | Vigente → RN-09 |
| TP RN-09 un cliente, a lo sumo un perfil (UNIQUE, 409) | Vigente (la tabla `perfil_cliente` no cambia) |
| TP RN-10 paginación `limit`/`offset` | **Superada**: envoltorio `{items,total,page,size,pages}` con `page`/`size` |
| TP RN-11 búsqueda por título sin distinguir mayúsculas, parámetro ligado | **Vigente** (la consigna lo confirma); ojo: en el Parcial **RN-11** es otra cosa (stock por movimientos) |
| TP RN-12 sin texto interno de la base | Vigente → RN-15 |
| SU-01 del TP (el stock no se descuenta) | **Superado** por RN-10/RN-11 |

## Requisitos no funcionales

Vigentes en TP y Parcial salvo lo indicado:

- **NF-01 Asincronía**: todos los handlers `async def`; ninguna llamada bloqueante; **bcrypt siempre fuera del bucle** (Parcial).
- **NF-02 Credenciales**: ninguna contraseña ni **clave de firma** en el código —tampoco como valor por defecto—, en `alembic.ini`, en el repositorio ni en la imagen. Si faltan en el entorno, la app no arranca (Parcial).
- **NF-03 SQL**: nunca por concatenación con datos del usuario.
- **NF-04 Carga perezosa prohibida**: toda relación leída se precarga en el repositorio (`joinedload` a uno, `selectinload` colecciones).
- **NF-05 Errores**: mensajes propios; nunca texto de la base ni traza; ninguna entrada inválida en 500.
- **NF-06 Unicidad**: garantizada por la base; sin consulta previa.
- **NF-07 Diagnóstico**: las consultas se ven en consola (`SQL_ECHO=true` o equivalente).
- **NF-08 Token** (Parcial): solo en la cookie HttpOnly; nunca en el cuerpo ni leído de la cabecera `Authorization`.
- **NF-09 Esquema**: solo con Alembic; la aplicación no usa `create_all`.
- **NF-10 Transacciones** (Parcial): ningún repositorio confirma; ningún servicio construye su Unit of Work; el Unit of Work no cierra la sesión.
- **NF-11 Contenedor** (despliegue del TP): imagen base `python:3.12-alpine`; la app no corre como root; ningún secreto dentro de la imagen.

## Excepciones globales

- Un proyecto que no levanta, que no crea su esquema con `alembic upgrade head` sobre una base vacía o que contiene credenciales reales en el repositorio, la imagen o el zip **no se corrige** hasta subsanar. Si el zip incluye `.git`, su historial también se revisa.
- Ningún `if` consulta antes si un id existe: se escribe y, si la base rechaza la FK, se responde 409.
- Si el despliegue no está accesible al corregir, el criterio se evalúa solo sobre `DEPLOY.md` y `evidencia/`; los casos D no comprobables no suman.
