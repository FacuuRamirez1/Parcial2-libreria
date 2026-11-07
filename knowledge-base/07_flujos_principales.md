# Flujos Principales

> Flujos 1-6: **TP caps 1-4 (implementado)**. Flujos P1-P11: **Parcial (pendiente)**. Donde el Parcial modifica un flujo del TP, el flujo del TP queda marcado como superado.

---

# Bloque A — TP caps 1-4 (implementado)

## Flujo 1: Registrar una venta *(superado por el Flujo P5)*
**Disparador**: `POST /ventas/` con `cliente_id` y `renglones`.
1. El router valida `VentaCreate` (≥ 1 renglón, sin `libro_id` repetido, `cantidad > 0`); si falla, 422 sin ejecutar el service.
2. El service lee los libros para copiar `precio` a `precio_unitario`.
3. Calcula `total = Σ cantidad × precio_unitario` con `Decimal`.
4. Crea `Venta` con sus `RenglonVenta` y hace commit. FK rechazada → `IntegrityError` traducido → 409.
5. Recarga con cliente y renglones (carga anticipada) y responde 201; agenda el aviso con `BackgroundTasks`.
*En el TP el stock no se descontaba.*

## Flujo 2: Alta de libro con autores *(modificado por P6: `stock_inicial` y movimiento)*
`POST /libros/` con `editorial_id`, `genero_id`, `autores`. Se crea `Libro` + `LibroAutor` sin consultar antes si los ids existen; ISBN repetido o FK rechazada → 409; 201 con el detalle.

## Flujo 3: Detalle de libro o de venta sin N+1 *(se mantiene; la precarga pasa al repositorio)*
Una consulta con `joinedload` (editorial, género, cliente) y `selectinload` (autorías con su autor, renglones con su libro); número fijo de consultas.

## Flujo 4: Perfil único del cliente *(se mantiene)*
`POST /clientes/{id}/perfil`; segundo perfil → 409 por UNIQUE.

## Flujo 5: Búsqueda de libros por título *(se mantiene; el listado pasa a `page`/`size`)*
Parámetro ligado (`ilike`); `' OR '1'='1` → lista vacía.

## Flujo 6: Esquema desde cero
`alembic upgrade head` aplica 0001 y 0002; `downgrade -1` + `upgrade head`; luego el script de datos. *(El Parcial agrega 0003 y 0004; ver Flujo P10.)*

---

# Bloque B — Parcial caps 1-6 (pendiente)

## Flujo P1: Registro de un cliente (RN-01, RN-02, RN-15)
**Disparador**: `POST /auth/registro` (`email`, `nombre`, `password`; `extra="forbid"`: no se acepta rol).
1. El contrato valida y limita la contraseña a 72 **bytes** (si no, 422).
2. El servicio calcula el hash bcrypt (`to_thread`, bajo semáforo) **antes** de abrir la transacción.
3. `async with uow`: inserta `usuario`, `asignacion_rol` (CLIENTE) y `cliente` (con `usuario_id`). Sin pre-consultar el correo.
4. Si el correo ya existe como usuario o como cliente, UNIQUE rechaza → `IntegrityError` traducido → **409** con mensaje propio; el UoW hace rollback y **no queda ninguna fila suelta**; el registro no se apropia de una ficha de cliente existente.
5. 201 sin `password_hash`.

## Flujo P2: Login (RN-07, RN-08)
**Disparador**: `POST /auth/login` (`email`, `password` ≤ 72 bytes).
1. Se cuenta en `intento_acceso` los fallos de ese `email`+`ip` en los últimos 60 s desde el último éxito. Si hay ≥ 5 → **429** con `Retry-After`, **sin calcular hash**, en pocos milisegundos.
2. Se busca el usuario; se verifica la contraseña contra su hash, o contra el **hash ficticio** (calculado en el lifespan) si el correo no existe → mismo 401, mismo cuerpo, tiempo parecido. Usuario inactivo → 401.
3. El intento (éxito o fallo) se anota con **sesión y transacción propias**, siempre confirmadas (queda aunque el fallo revierta la petición).
4. Éxito: JWT (`sub`, `exp`, roles vigentes) → `Set-Cookie: access_token=…; HttpOnly; SameSite=Lax; Max-Age=<duración>` (+ `Secure` según config). Cuerpo `{mensaje, debe_cambiar_password, expira_en_segundos}`, sin token.

## Flujo P3: Petición autenticada y autorizada (RN-04)
1. `get_usuario_actual` lee `request.cookies["access_token"]`; sin cookie, token inválido/vencido, usuario inexistente o inactivo → **401**.
2. `requiere_rol("ADMIN")` consulta en la base los roles **vigentes** (no revocados, no vencidos) en la misma sesión que usa el UoW (una conexión por petición); sin el rol → **403**.
3. El grupo protegido aplica además el control de cambio obligatorio: `debe_cambiar_password` → 403 salvo `/auth`.
4. El handler llama al servicio con el UoW.

## Flujo P4: Revocación con sesión abierta (C-07, RN-04, RN-05, RN-16)
1. ADMIN: `DELETE /usuarios/{id}/roles/{rol}` → el servicio escribe `revocada_en` (no borra) y deja una línea en `evento_seguridad`, **en el mismo UoW**.
2. Si el ADMIN se revoca su propio ADMIN, o quedaría sin administradores vigentes → 409.
3. La sesión del revocado conserva la cookie; su **siguiente petición da 403** (los roles se leen de la base). `/auth/yo` muestra la diferencia entre roles vigentes y los del token.
4. Asignar con vencimiento: `vence_en` sin zona horaria o en el pasado → 422 (no 409). Reasignar un rol vencido cierra la fila anterior y abre una nueva; reasignar uno abierto → 409 (índice único parcial).

## Flujo P5: Venta con descuento de stock (RN-09, RN-10, RN-11)
**Disparador**: `POST /ventas` (VENDEDOR/ADMIN) con `cliente_id` y `renglones`.
1. Contrato: ≥ 1 renglón, sin repetidos, `cantidad > 0`, `extra="forbid"` (nada de precio ni total).
2. `async with uow`: lee los libros vigentes (los dados de baja no se pueden vender), copia el precio, calcula el total con `Decimal`, inserta `venta` y `renglon_venta`, y por cada renglón descuenta el stock y agrega un `movimiento_stock` (cantidad negativa) **por el único punto de escritura de stock**.
3. Libro sin stock suficiente, libro inexistente / dado de baja o cliente inexistente → 409; **rollback de todo**: ni venta, ni renglones, ni descuentos, ni movimientos (C-11, C-12).
4. Confirmada: 201; **después** de enviar la respuesta y solo si se confirmó, `BackgroundTasks` ejecuta el aviso (`sleep(0.5)` + log) (C-10, D-08).
5. Invariante: `libro.stock` = suma de movimientos, en los cinco libros (se verifica tras cada caso).

## Flujo P6: Reposición (RN-11)
`POST /libros/{id}/reponer` (ADMIN): un solo UoW suma stock y agrega un movimiento positivo; libro dado de baja → 409; id inexistente → 404. `GET /libros/{id}/movimientos` lista el historial. Un error de carga se corrige con **otro movimiento** compensatorio; nunca UPDATE/DELETE (trigger).

## Flujo P7: Baja lógica y re-alta de ISBN (RN-01, RN-13, C-13)
1. `DELETE /libros/{id}` (ADMIN) → `soft_delete` (`borrado_en = now()`), **204**. Desaparece del catálogo.
2. `POST /libros` con el mismo ISBN → **201** (el índice único parcial solo mira los vigentes).
3. Un segundo libro vigente con ese ISBN → **409**.
4. `GET /ventas/{id}` de una venta vieja sigue mostrando el título del libro dado de baja (la lectura usa `get_by_id_including_deleted` / precarga sin filtro de baja).

## Flujo P8: Detalle de venta como dueño o personal (RN-14, C-08, C-15)
1. `GET /ventas/{id}` (sin `requiere_rol`): el router entrega usuario actual y UoW; el servicio decide: ¿es personal vigente? ¿es el cliente dueño (`venta.cliente.usuario_id == usuario.id`)? Si no → **403**; si la venta no existe → 404.
2. La consulta usa carga anticipada (cliente, renglones, libro de cada renglón, incluso dado de baja): **mismo número de consultas con 2 y con 4 renglones**.
3. `GET /mis-ventas` devuelve solo las del cliente asociado al usuario actual, con el envoltorio de paginación.

## Flujo P9: Cambio obligatorio de contraseña (C-09, RN-06, RN-16)
1. Un usuario con `debe_cambiar_password` (p. ej. `nuevo@example.com`) inicia sesión; cualquier ruta protegida → 403, salvo `/auth`.
2. `POST /auth/cambiar-password` (actual ≤ 72 bytes, nueva ≤ 72 bytes): hash fuera de la transacción; en un UoW actualiza el hash, pone `debe_cambiar_password=false` y deja un `evento_seguridad`.
3. **La misma cookie** sirve en la petición siguiente (no se emite token nuevo ni se invalidan sesiones).

## Flujo P10: Listado paginado (C-16)
`GET /libros?titulo=ficc&size=1` → `{items:[…], total:1, page:1, size:1, pages:1}`; `page=2` → 422 ("La página 2 no existe: hay 1"); `size=500` → 422; sin resultados → una página vacía con `total=0`. `total` cuenta con los mismos filtros. `PATCH /libros/{id}` con `stock` → 422 (`extra="forbid"`); PATCH parcial cambia solo lo enviado.

## Flujo P11: Esquema desde cero y solo agregado (C-14)
`alembic upgrade head` (0001→0004) sobre base vacía; `python seed.py`. En psql, `UPDATE`/`DELETE` sobre `movimiento_stock` → rechazados por el trigger (`test/solo_agregado.sql`).

## Flujo P12: Imagen Docker y despliegue del TP (D-01..D-08)
1. `docker build -t libreria .` en `despliegue/` (base `python:3.12-alpine` < 100 MB; capa de dependencias antes del código).
2. `docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped --env-file <archivo> libreria`; al arrancar: `alembic upgrade head` y luego uvicorn en `0.0.0.0`. Base inaccesible (o sin `DATABASE_URL`) → el contenedor **termina con error**, no queda sirviendo (D-05).
3. `docker ps` → `healthy` (HEALTHCHECK con `127.0.0.1`) (D-02).
4. Carga de datos con `docker exec libreria …` (comando del README del TP); desde afuera: `GET /health/ready` 200, `GET /libros/`, `POST /ventas/` 201 (D-03); `docker logs libreria` muestra el aviso tras la línea de respuesta (D-08).
5. `docker rm -f libreria` + mismo `docker run`: vuelve a `healthy`, los datos siguen, las migraciones no se repiten (D-04).
6. Inspección: no hay `.env` (`docker run --rm --entrypoint ls <imagen> -a /app`), `env` no muestra `DATABASE_URL` (D-06), `docker exec libreria id` no es root (D-07).
7. Actualizar: rebuild → `docker rm -f` → `docker run`; los datos viven en la base del servidor.
