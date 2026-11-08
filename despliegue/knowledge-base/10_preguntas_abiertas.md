# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — Pre-consulta de ids vs lectura del precio
**Consigna dice (Ejercicio 5)**: en el alta del libro ningún `if` consulta antes si un id existe.
**Consigna dice (RN-06)**: en la venta el servidor lee el precio del libro de la base.
**Impacto**: para la venta hay que leer el libro sí o sí; hay que decidir cómo se responde si no existe.
**Resolución propuesta**: leer los libros en una consulta, comparar contra los ids pedidos y responder 409 con mensaje propio (ver SU-03).

### IN-02 — Extracción del PDF con tablas entrelazadas
**El texto extraído**: mezcla columnas en la tabla de endpoints, en los casos C-01 a C-08 y en las reglas de negocio.
**Impacto**: el listado exacto de endpoints y las asignaciones caso → resultado son inferidas.
**Resolución propuesta**: contrastar `02_descripcion_general.md` y `09_decisiones_y_supuestos.md` con el PDF original antes de proponer los changes 4 y 5.
**Resuelta (listado de endpoints)**: verificado contra el PDF (se quitó `GET /autores/`). Los códigos de `GET /ventas/{id}` quedan inferidos; la asignación de resultados de los casos C-01 a C-08 no se revisó en esta pasada.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| ~~Alta~~ | ~~¿El listado de endpoints (SU-04) coincide exactamente con el PDF?~~ **Resuelta:** verificado contra el PDF; se quitó `GET /autores/`, que no figura | ~~Change 4~~ | Grupo (revisando el PDF) |
| ~~Alta~~ | ~~¿Qué responde una venta con libro o cliente inexistente: 409 (SU-02)?~~ **Resuelta:** el PDF lista 201, 409, 422 (sin 404) en `POST /ventas/`, lo que confirma 409 | ~~Change 5~~ | Grupo / docente |
| Media | ¿Se descuenta stock al vender (SU-01)? | Change 5 | Docente |
| Media | ¿Quién toma cada uno de los 7 changes? | Roadmap | Grupo |
| Media | ¿Cuál es la fecha de entrega? | Roadmap | Grupo |
| Baja | ¿Se agregan tests automáticos además de los `.http`? | Ninguno (fuera de la rúbrica) | Grupo |
| ~~Baja~~ | ~~¿Dónde vive exactamente el script de datos iniciales (`scripts/seed.py`)?~~ **Resuelta:** `scripts/seed.py`, creado en C-03 (ver design.md del change archivado) | ~~Change 1 o 4~~ | Grupo |
| ~~Baja~~ | ~~¿Qué incluye `GET /health/ready` en su respuesta ("estado de la base")?~~ **Resuelta:** `200 {"estado":"listo","base":"conectada"}`; fallo o timeout (3 s) también `200` con `{"estado":"no listo","base":"sin conexión"}` (el PDF lista sólo 200 para este endpoint), sin texto del driver | ~~Change 1~~ | Grupo |
