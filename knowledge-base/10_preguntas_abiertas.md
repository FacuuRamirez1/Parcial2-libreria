# Preguntas Abiertas

> IN-01/IN-02 y preguntas ya resueltas: **TP caps 1-4**. IN-03 en adelante y las filas nuevas: **Parcial caps 1-6**.

## Inconsistencias detectadas

### IN-01 — Pre-consulta de ids vs lectura del precio (TP) — *resuelta*
Resolución: leer los libros, comparar contra los ids pedidos y responder 409 (SU-03). En el Parcial, la lectura incluye stock y baja lógica.

### IN-02 — Extracción del PDF con tablas entrelazadas (TP) — *resuelta en el TP*
Listado de endpoints del TP verificado contra el PDF. Ver IN-03 para el mismo problema en el Parcial.

### IN-02b — `seed.py` en la raíz (Parcial) vs `scripts/seed.py` (TP)
**Consigna del Parcial dice**: `seed.py` en la estructura obligatoria y `python seed.py` en el README/casos. **El repo tiene**: `scripts/seed.py` del TP.
**Resolución propuesta**: en `parcial/`, crear `seed.py` en la raíz con el contenido nuevo (C-14). `scripts/seed.py` del TP queda para el snapshot de `despliegue/` (el "comando de datos iniciales" de su README). Decidir en C-14 si se elimina o delega el de `scripts/`.

### IN-03 — Tablas del Parcial extraídas con columnas entrelazadas
**Afecta**: la tabla "Endpoints de referencia" (códigos y algunos "Quién"), la de reglas RN (etiquetas desalineadas una fila), el modelo de dominio (restricciones y columnas intercaladas) y los casos C/D (resultados desordenados).
**Qué se hizo**: reconstrucción fila a fila con el orden de aparición y las citas cruzadas del texto (RN-xx citados en los ejercicios; casos descritos en el texto de cada ejercicio). El PDF (`Parcial_Cap1a6_Consigna.pdf`) tiene el mismo entrelazado, así que no resuelve la duda.
**Inciertos**: códigos de `POST/GET/DELETE /usuarios…`, `/eventos`, `reponer`, `movimientos`, `logout` y `cambiar-password`; la columna "Quién" de las rutas `…/{id}/libros` (la tabla las deja en ADMIN, pero el catálogo es público). Marcados con (*) en `03_actores_y_roles.md`.
**Resolución propuesta**: contrastar visualmente con el PDF antes de C-11/C-12; ante duda, ser permisivo en tests y estricto con 401/403/404/409/422 documentados.

### IN-04 — Rutas del TP que el Parcial no lista
`GET /editoriales/{id}`, `GET /autores/{id}`, `GET /clientes…` adicionales y otras del TP no figuran en la tabla del Parcial; la regla del proyecto dice "NUNCA exponer rutas fuera de la tabla". **Propuesta**: conservar las del TP (el Parcial parte "de su propio TP") en el grupo protegido (ADMIN) o abierto según su familia, sin ampliar. **Decisor**: docente.

### IN-05 — Stock existente vs invariante "stock = suma de movimientos"
Si ya hay libros con `stock` y sin movimientos, la invariante se rompe. **Propuesta**: 0003 (o el seed) crea un movimiento "Stock inicial" por libro; en `parcial/` la base se reconstruye con `seed.py` (SU-13).

### IN-06 — `main.py` en la raíz (consigna) vs `app/main.py` (TP y Dockerfile)
La tabla de estructura lista `main.py` junto a `seed.py`; el Dockerfile arranca `app.main:app`. **Propuesta**: mantener `app/main.py` (SU-07).

### IN-07 — `DATABASE_URL` (TP/despliegue) vs `POSTGRES_*` (Parcial)
Son dos proyectos con dos configuraciones. El `.env`/`env.example` de `despliegue/` usa `DATABASE_URL` + `SQL_ECHO=false`; el de `parcial/` usa `POSTGRES_*` + clave JWT. Riesgo: pegar un `env.example` en la carpeta equivocada o que el README del parcial mencione `DATABASE_URL`. **Propuesta**: documentar la diferencia en ambos README y en DEPLOY.md.

### IN-08 — Documentos del proyecto desactualizados respecto del Parcial
`CLAUDE.md`/`AGENTS.md` y `CHANGES.md` dicen "7 changes, ninguno extra", "NUNCA agregar repositorios, UoW, autenticación, movimientos de stock, borrado lógico ni triggers" y "listados con limit/offset". El Parcial lo contradice (DD-07, DD-09). Esta actualización **no** los modifica. **Pendiente**: re-sincronizar `CHANGES.md` (C-08..C-16) y las reglas duras antes del primer `/opsx:propose C-08`.

### IN-09 — `GET /health/ready`: 200 (TP) vs 503 (Parcial)
El TP responde siempre 200 (decisión de C-01 por el PDF del TP). El Parcial pide 503 si la base no contesta. En `parcial/` (C-08) cambia a 503. En `despliegue/` el snapshot queda con 200 siempre; el HEALTHCHECK sobre `/health/ready` es consistente en ambos casos, pero con 200-siempre el contenedor puede figurar `healthy` con la base caída. La consigna del ej. 9 permite corregir "una ruta de salud que no responde como pedía su consigna" y anotarlo en DEPLOY.md; la del TP pedía 200. **Propuesta**: no tocarlo en `despliegue/`.

### IN-10 — Descripción del límite de intentos
RN-07: "5 intentos fallidos … en 60 segundos, el login responde 429" y C-05: "seis intentos fallidos seguidos: el sexto, 429". Coherente: los 5 primeros devuelven 401 y el 6.º 429. "Misma dirección" = IP del cliente (Settings/proxy en el VPS podría ocultar la IP real; no se evalúa).

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| Alta | ¿`seed.py` va en la raíz (consigna) o se mantiene `scripts/seed.py` (IN-02b)? | C-14 | Grupo / docente |
| Alta | Códigos y roles inciertos de la tabla de endpoints (IN-03) y rutas del TP no listadas (IN-04) | C-11, C-12, C-13 | Docente |
| Alta | Re-sincronizar `CHANGES.md`, `CLAUDE.md` y `AGENTS.md` con C-08..C-16 (IN-08) | Primer `/opsx:propose` del Parcial | Grupo |
| Media | ¿Nombre del grupo (para `Parcial_Cap1a6_<NombreDelGrupo>.zip`) y fecha límite? | C-14 / entrega | Grupo |
| Media | ¿Cómo se llama la variable de la clave JWT (`JWT_SECRET_KEY`?) y qué valores por defecto de configuración (costo bcrypt, semáforo, pool, duración)? | C-08 | Grupo |
| Media | ¿Puerto asignado, URL pública, host de la base y acceso SSH al VPS? | C-16 | Cátedra |
| Media | ¿Qué tag exacto de git para el snapshot (sobre `f1b9b48`) y cómo se copia a `despliegue/`? | C-15 | Grupo |
| Media | ¿El comando de datos iniciales del TP en el contenedor es `python scripts/seed.py`? (README del TP) | C-16, D-03 | Grupo |
| Media | ¿Quién toma cada change C-08..C-16? | Roadmap | Grupo |
| Baja | ¿Registro inicia sesión automáticamente? (SU-10) | C-11 | Grupo |
| Baja | ¿`/auth/logout` y `/auth/cambiar-password` exigen sesión (401)? | C-11 | Grupo |
| Baja | ¿Tests automáticos además de los `.http`? | Ninguno | Grupo |
| ~~Alta~~ | ~~¿El listado de endpoints del TP coincide con el PDF?~~ **Resuelta** (TP) | ~~C-04~~ | — |
| ~~Alta~~ | ~~¿Venta con libro o cliente inexistente: 409?~~ **Resuelta** (TP) y reafirmada por C-12 del Parcial | ~~C-05~~ | — |
| ~~Media~~ | ~~¿Se descuenta stock al vender (SU-01)?~~ **Resuelta por el Parcial**: sí, vía movimientos (RN-10/RN-11) | ~~C-05~~ | — |
| ~~Baja~~ | ~~¿Dónde vive el script de datos iniciales?~~ **Resuelta en el TP**: `scripts/seed.py`; **reabierta para el Parcial** (IN-02b) | ~~C-01 o C-04~~ | — |
| ~~Baja~~ | ~~¿Qué incluye `GET /health/ready`?~~ **Resuelta en el TP**: 200 siempre; **cambia en el Parcial** (IN-09) | ~~C-01~~ | — |
