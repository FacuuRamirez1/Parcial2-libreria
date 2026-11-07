# Decisiones y Supuestos

> **DD-01..DD-06 / SU-01..SU-06: TP caps 1-4 (implementado).** Se conservan; cada una indica si queda vigente o **superada** por el Parcial. **DD-07.. / SU-07..: Parcial caps 1-6 (pendiente).**

## Decisiones del TP caps 1-4 (implementado)

### DD-01 — Un change por ejercicio — *vigente (extendida por DD-07)*
**Decisión**: el roadmap del TP tiene exactamente 7 changes (C-01..C-07), uno por ejercicio. **Estado**: archivados e intactos. La regla "un change por ejercicio" se mantiene, pero el Parcial usa su propio mapa (DD-07), que **no** es 1:1 (9 changes para 10 ejercicios).

### DD-02 — Prioridad: cumplir la rúbrica — *vigente*
Se implementa lo que pide la consigna, con nombres y códigos exactos, y nada más. Los extras no suman. *Matiz: el Parcial sí exige Docker para el despliegue (DD-13).*

### DD-03 — PostgreSQL local por integrante — *vigente para `parcial/`*
Cada integrante instala PostgreSQL 16 y usa su `.env`; sin Compose. En el despliegue la base es la del servidor (DD-13).

### DD-04 — Datos iniciales con script Python asincrónico — *vigente; ubicación y contenido superados*
El seed es un script async. TP: `scripts/seed.py`. El Parcial pide `seed.py` con otro contenido (ver DD-12 e IN-02).

### DD-05 — Garantías en la base, no en consultas previas — *vigente*
Unicidad y FKs se resuelven con `IntegrityError` → 409. Se amplía con índices únicos parciales y trigger.

### DD-06 — Dinero con Decimal — *vigente*
`Decimal` y `NUMERIC(10,2)`/`NUMERIC(12,2)`; nunca `float`.

## Decisiones del Parcial (pendiente)

### DD-07 — Roadmap del Parcial = changes C-08..C-16
**Decisión**: los changes del Parcial continúan la numeración: C-08 `settings-y-base-de-capas`; C-09 `modulos-a-repositorios-uow` (migrar los 7 módulos existentes y el envoltorio de paginación); C-10 `modelos-acceso-stock-migraciones` (modelos nuevos + migración 0003 autogenerada + 0004 trigger a mano); C-11 `autenticacion`; C-12 `autorizacion-roles-y-rutas`; C-13 `stock-movimientos-baja-logica-ventas`; C-14 `seed-casos-y-evidencia`; C-15 `imagen-docker-tp-cap1a4`; C-16 `despliegue-vps`. C-01..C-07 quedan archivados e intactos.
**Contexto**: el Parcial continúa el TP. **Justificación**: no reabrir trabajo evaluado y mantener historial limpio.
**Trade-offs**: la regla de `CLAUDE.md` "7 changes, ninguno extra" queda desactualizada (ver IN-08); hay que re-sincronizar `CHANGES.md` y `CLAUDE.md`/`AGENTS.md` (fuera del alcance de esta actualización de la KB).

### DD-08 — Lo ya implementado no se rehace
**Decisión**: solo se modifica donde haga falta conectarlo con lo nuevo: refactor a UoW, `Cliente.usuario_id`, `Libro.borrado_en`, `stock`→movimientos, listados con envoltorio, `Settings`.
**Justificación**: la consigna parte "de su propio TP entregado". **Trade-off**: C-09 toca los 7 módulos a la vez; conviene un refactor guiado por los tests/`.http` del TP.

### DD-09 — Reemplazos explícitos de lo del TP
- Servicios con sesión → servicios con UoW (**supera** "Service con sesión por parámetro" del TP).
- `limit`/`offset` → `{items,total,page,size,pages}` (**supera** TP RN-10).
- `UNIQUE(isbn)` → índice único parcial (**supera** TP RN-01).
- `stock` editable por PATCH/alta → solo por movimientos (**supera** SU-01).
- `GET /health/ready` siempre 200 → 503 si la base no contesta (**supera** la decisión del change C-01 del TP).
- `python-dotenv` → `pydantic-settings`; `DATABASE_URL` → `POSTGRES_*` (en `parcial/`).
- "Fuera de alcance: auth, repositorios, UoW" → ahora **dentro**.

### DD-10 — Autorización en la base, token solo informativo
Los roles se leen de `asignacion_rol` en cada petición (RN-04). El JWT lleva los roles vigentes al emitirlo, solo informativos. `usuario` no tiene columna `rol`. **Justificación**: revocar quita permiso de inmediato.

### DD-11 — Cookie HttpOnly, sin `Authorization`, sin invalidación de sesiones
Login tradicional con cookie; cambiar la contraseña no invalida sesiones ni emite token nuevo. **Trade-off**: aceptado por la consigna.

### DD-12 — Seed del Parcial reemplaza al del TP en `parcial/`
Datos de la sección "Datos iniciales" de la consigna, con movimientos coherentes (stock = suma). La ubicación (`seed.py` en la raíz vs `scripts/seed.py`) queda en IN-02; propuesta: `seed.py` en la raíz (lo que pide la consigna y el README: `python seed.py`), reutilizable desde `scripts/` si se desea.

### DD-13 — Despliegue Docker sobre un snapshot del TP caps 1-4
**Decisión**: tag de git sobre `f1b9b48` ("Tests y detalles finales corregidos"), copiado a `despliegue/`. Ese TP usa `DATABASE_URL` (no `POSTGRES_*`) y **no lleva ninguna modificación del parcial**. Solo se agregan `Dockerfile`, `.dockerignore`, `env.example`, `DEPLOY.md`; la lógica no se toca (salvo defecto propio, anotado en DEPLOY.md).
**Justificación**: la consigna lo exige. **Trade-off**: dos bases de código con configuraciones distintas; riesgo de confundir las variables (IN-07).

### DD-14 — Sesión propia para `intento_acceso`
Única escritura que no comparte la transacción de la petición (el fallo contado es el que la revierte). Va documentada con un comentario de tres puntos (qué, por qué, costo).

### DD-15 — Alcance negativo confirmado
Sigue fuera de alcance: concurrencia/bloqueos (cap. 7), Redis/colas (cap. 8) y el rol de base sin permiso sobre `movimiento_stock` (solo se pide el trigger; tener ambos sería defensa en profundidad).

### DD-16 — Política de commits
Las reglas del proyecto mantienen: no buildear ni commitear sin pedido explícito del usuario; commits convencionales.

## Supuestos del TP (implementado)

### SU-01 — El stock no se descuenta al vender — **SUPERADO**
Reemplazado por RN-10 / RN-11 del Parcial (la venta descuenta stock y deja movimientos).

### SU-02 — Venta con libro o cliente inexistente responde 409 — *vigente (confirmado)*
Confirmado contra el PDF del TP y reafirmado por C-12 del Parcial (409 en los tres casos: cliente, libro inexistente, libro dado de baja).

### SU-03 — En ventas se lee el libro antes de insertar — *vigente*
El servidor igual debe leer el precio (copiado del libro). Ahora además lee el stock; libro inexistente o dado de baja → 409 con mensaje propio.

### SU-04 — Lista de endpoints reconstruida — *vigente para el TP; ver IN-03 para el Parcial*
Verificada contra el PDF del TP (se quitó `GET /autores/`).

### SU-05 — El cliente puede existir sin perfil — *vigente*
### SU-06 — Grupo con reparto por ejercicio — *vigente; reparto por change C-08..C-16 pendiente*

## Supuestos del Parcial (pendiente)

### SU-07 — `main.py` del Parcial es `app/main.py`
**Supuesto**: la tabla de estructura lista `main.py`, pero el Dockerfile pide `app.main:app`. Se mantiene `app/main.py` del TP.
**Riesgo si es falso**: el corrector busca `main.py` en la raíz. **Cómo validar**: preguntar al docente (IN-06).

### SU-08 — Algoritmo del token HS256 y duración 1800 s
**Supuesto**: JWT con HS256 y duración de 30 minutos (el ejemplo de login dice `expira_en_segundos: 1800`), ambos en la configuración. **Riesgo**: bajo.

### SU-09 — Contraseña mínima, semáforo y dirección del cliente
**Supuesto**: la consigna no fija largo mínimo de contraseña, tamaño del semáforo ni el origen de `ip` (`request.client.host`); se eligen valores razonables y se declaran en `Settings`/README.

### SU-10 — Registro no inicia sesión
**Supuesto**: `POST /auth/registro` devuelve 201 sin cookie; el cliente luego hace login. **Riesgo**: bajo.

### SU-11 — Familia de rutas `…/{id}/libros` y rutas del TP no listadas
**Supuesto**: se mantienen las del TP no listadas en la tabla del Parcial, protegidas como su familia; las `…/{id}/libros` siguen la tabla (ADMIN). Ver IN-03 e IN-04.

### SU-12 — Quién puede crear ventas
**Supuesto**: `POST /ventas`, `GET /ventas` y las rutas de clientes son para `VENDEDOR` y `ADMIN` (la columna "Quién" de la tabla entrelazada se reconstruyó fila a fila; el caso C-08 confirma que un VENDEDOR no puede crear libros).

### SU-13 — Migración de datos existentes
**Supuesto**: la base de `parcial/` se reconstruye desde cero con `seed.py`; no se migran datos del TP. Si hubiese libros previos, 0003 debe insertar sus movimientos "Stock inicial".
