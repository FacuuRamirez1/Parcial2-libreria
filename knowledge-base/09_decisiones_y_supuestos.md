# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Un change por ejercicio
**Decisión**: el roadmap tiene exactamente 7 changes, uno por ejercicio de la consigna.
**Contexto**: pedido explícito del usuario para el trabajo en grupo.
**Alternativas consideradas**: dividir por módulo o por capa.
**Justificación**: cada ejercicio es una unidad evaluable y tiene su peso en la rúbrica.
**Trade-offs aceptados**: los ejercicios 2 y 3 comparten modelos y el 5 y el 6 comparten el módulo de libros y ventas; el orden de los changes importa.

### DD-02 — Prioridad: cumplir la rúbrica
**Decisión**: se implementa lo que pide la consigna, con los nombres y códigos exactos, y nada más.
**Contexto**: la corrección usa los nombres de tablas y columnas, y los casos C-01 a C-08.
**Alternativas consideradas**: priorizar mantenibilidad o velocidad.
**Justificación**: el criterio de éxito es la nota; los extras no suman.
**Trade-offs aceptados**: sin tests automáticos, Docker ni funciones extra.

### DD-03 — PostgreSQL local por integrante
**Decisión**: cada integrante instala PostgreSQL 16 y usa su `.env`; no hay Docker Compose.
**Contexto**: la consigna pide `env.example` y pasos de arranque, no contenedores.
**Alternativas consideradas**: Docker Compose en el repo; base remota compartida.
**Justificación**: preferencia del grupo y menos piezas fuera de la consigna.
**Trade-offs aceptados**: posibles diferencias de entorno entre integrantes (versión, usuario, puerto).

### DD-04 — Datos iniciales con script Python asincrónico
**Decisión**: el seed es un script async que reutiliza los modelos y la sesión.
**Contexto**: los casos de prueba exigen un script o comando que deje la base en estado conocido.
**Alternativas consideradas**: script SQL con `psql`.
**Justificación**: coherente con el stack y fácil de reiniciar.
**Trade-offs aceptados**: depende del código de la aplicación; si los modelos fallan, el seed también.

### DD-05 — Garantías en la base, no en consultas previas
**Decisión**: unicidad y FKs se resuelven con el `IntegrityError` traducido a 409.
**Contexto**: requisito no funcional de la consigna (RN-01, RN-02, RN-09).
**Justificación**: evita condiciones de carrera y respeta lo exigido.

### DD-06 — Dinero con Decimal
**Decisión**: `Decimal` y `NUMERIC(10,2)` o `NUMERIC(12,2)`; nunca `float`.

## Supuestos inferidos

### SU-01 — El stock no se descuenta al vender
**Supuesto**: registrar una venta no modifica `libro.stock`.
**Origen**: la consigna no lo menciona en ninguna regla de negocio.
**Riesgo si es falso**: el corrector podría esperar un stock decreciente o un rechazo por falta de stock.
**Cómo validar**: confirmar con el docente o releer el PDF.

### SU-02 — Venta con libro o cliente inexistente responde 409
**Supuesto**: el caso C-05 se resuelve con 409 y mensaje propio.
**Origen**: el PDF se extrajo con columnas entrelazadas; la asignación de resultados a C-04/C-05 se infirió.
**Riesgo si es falso**: código HTTP incorrecto (404 en vez de 409).
**Cómo validar**: contrastar con el PDF original.
**Confirmado contra el PDF**: `POST /ventas/` lista 201, 409, 422 (sin 404), lo que confirma 409 para libro o cliente inexistente.

### SU-03 — En ventas se lee el libro antes de insertar
**Supuesto**: la prohibición de "consultar antes si un id existe" aplica al alta de libro. En la venta el servidor igual debe leer el precio del libro (RN-06), así que un libro inexistente se detecta al leer y se traduce a 409 con mensaje propio; la inexistencia del cliente la rechaza la FK.
**Origen**: tensión entre RN-06 y el requisito de no pre-consultar ids.
**Riesgo si es falso**: penalización de la rúbrica en el Ejercicio 5.
**Cómo validar**: consultar al docente.

### SU-04 — Lista de endpoints reconstruida
**Supuesto**: la lista de `02_descripcion_general.md` es correcta.
**Origen**: la tabla del PDF está maquetada en columnas entrelazadas.
**Riesgo si es falso**: falta o sobra algún endpoint.
**Cómo validar**: contrastar con el PDF original antes de la propuesta del change.
**Resolución (verificado contra el PDF)**: el listado coincide salvo una diferencia, ya corregida: se quitó `GET /autores/`, que no está en el PDF. Los códigos por endpoint están en `02_descripcion_general.md`. Único dato inferido: los códigos de `GET /ventas/{id}` (200, 404), porque el PDF los cortó.

### SU-05 — El cliente puede existir sin perfil
**Supuesto**: el perfil se agrega después con `POST /clientes/{id}/perfil`.
**Origen**: "un cliente tiene como máximo un perfil" y la existencia de ese endpoint.
**Riesgo si es falso**: ninguno relevante.

### SU-06 — Grupo con reparto por ejercicio
**Supuesto**: los integrantes se reparten los 7 changes.
**Origen**: "trabajo en grupo" y la regla de un change por ejercicio.
**Riesgo si es falso**: el roadmap debe replantear el paralelismo.
