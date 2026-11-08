# Design

## Contexto

C-10 ya creó `movimiento_stock` (solo agregado por trigger), `libro.borrado_en` y el índice único parcial del ISBN. C-12 ya dejó `requiere_rol` y la sesión compartida. C-13 conecta esas piezas con el comportamiento del Ejercicio 6 (parte 2) y el Ejercicio 8: stock por movimientos, baja lógica, re-alta de ISBN, venta atómica y lecturas de ventas propias. No hay migración nueva.

## Decisiones

### D-01 — Punto único de escritura de stock

`app/modules/libros/stock.py` expone:

```python
async def registrar_movimiento(
    uow, *, libro: Libro, cantidad: int, motivo: str,
    usuario_id: int, venta_id: int | None = None,
) -> MovimientoStock:
    libro.stock += cantidad
    uow.session.add(libro)
    mov = MovimientoStock(
        libro_id=libro.id, venta_id=venta_id, usuario_id=usuario_id,
        cantidad=cantidad, motivo=motivo,
    )
    uow.session.add(mov)
    await uow.session.flush()
    return mov
```

- Es el **único** lugar que asigna `libro.stock`. Lo usan alta, reposición y venta.
- Recibe cualquier Unit of Work (libros o ventas): solo necesita `uow.session`.
- `cantidad = 0` no se permite (CHECK); el alta con `stock_inicial = 0` no crea movimiento.
- El `flush()` deja el id del movimiento y mantiene la transacción abierta; el commit es del UoW.

### D-02 — Alta con `stock_inicial`

- `LibroCreate.stock` se reemplaza por `stock_inicial` (`ge=0`, `extra="forbid"`).
- El servicio crea `Libro(..., stock=0)`, hace `add` (flush → id), y si `stock_inicial > 0` llama a `registrar_movimiento(+stock_inicial, "Stock inicial")`. La respuesta sigue exponiendo `stock`.
- Si el alta falla (ISBN/FK/CHECK), el UoW revierte libro, autorías y movimiento juntos.

### D-03 — Reposición

- `ReposicionIn { cantidad: int = Field(gt=0) }` con `extra="forbid"`.
- El repositorio busca el libro **incluyendo dados de baja** para distinguir 404 (no existe) de 409 (dado de baja).
- `POST /libros/{id}/reponer` responde 200 con `LibroDetalleRead` actualizado.

### D-04 — Baja lógica y re-alta

- `LibroRepository` pasa a `SoftDeleteRepository[Libro]`; `get_by_id`, `get_all`, `get_all_filtrado` y `count_filtrado` filtran `borrado_en IS NULL`.
- `DELETE /libros/{id}` busca con `get_by_id` (vigente); si no está → 404; si está → `soft_delete` → 204.
- El alta con un ISBN dado de baja lo acepta el índice único parcial; un segundo vigente lo rechaza el `IntegrityError` → 409 del handler global. Sin pre-consultas.
- Vender/reponer un libro dado de baja: el repositorio de ventas lee solo vigentes; si falta alguno → 409. Reponer usa `get_by_id_including_deleted` y responde 409 si `borrado_en` no es nulo.

### D-05 — Venta atómica con stock

- `crear_venta(uow, datos, usuario_id)` dentro de un solo `async with uow`:
  1. lee los libros vigentes con `select(Libro).where(Libro.id.in_(ids), Libro.borrado_en.is_(None))`;
  2. si faltó alguno → 409;
  3. valida stock de todos los renglones **antes** de escribir; si no alcanza → 409;
  4. calcula total con `Decimal`;
  5. crea `Venta` + `RenglonVenta` y hace `add` (flush);
  6. por cada renglón llama a `registrar_movimiento(-cantidad, "Venta", usuario_id, venta.id)`.
- Cualquier excepción dentro del bloque revierte todo (UoW). El `IntegrityError` (cliente inexistente) se traduce a 409.
- El router agenda `BackgroundTasks` **después** de que `crear_venta` retorna (commit ya hecho).

### D-06 — Decisión de dueño en el detalle de venta

- `GET /ventas/{id}` deja de usar `requiere_rol`; queda en el grupo protegido (solo autenticación, 401 sin cookie).
- El router pasa `UsuarioActual`; el servicio:
  1. carga la venta con `get_con_detalle` → 404 si no existe;
  2. consulta los roles vigentes con `AsignacionRolRepository(uow.session)` (misma sesión);
  3. permite si hay `VENDEDOR`/`ADMIN` vigente o si `venta.cliente.usuario_id == usuario.id`;
  4. si no → 403.
- El detalle mantiene `joinedload(cliente)` + `selectinload(renglones → libro)`; el libro dado de baja se sigue mostrando (sin filtro de `borrado_en` en la relación).

### D-07 — `GET /mis-ventas`

- Ruta en el grupo protegido, sin `requiere_rol` (solo autenticación).
- Busca `Cliente` por `usuario_id`; si no hay ficha → página vacía (`total=0`).
- Reutiliza `listar_ventas(uow, pag, cliente_id=...)` para no duplicar la precarga ni la paginación.

### D-08 — Arnés de pruebas pytest

- `tests/conftest.py` crea una base `libreria_test` (asyncpg contra `postgres`), corre `alembic upgrade head` por subprocess con variables de entorno de prueba, y por test hace `TRUNCATE ... RESTART IDENTITY CASCADE` (el trigger es por fila; TRUNCATE no lo dispara).
- La app se levanta con `app.router.lifespan_context(app)` y `httpx.AsyncClient(transport=ASGITransport(app))`.
- Los usuarios ADMIN/VENDEDOR/CLIENTE se insertan directo con bcrypt y sus `asignacion_rol`; el login se hace por `POST /auth/login` para obtener la cookie real.
- Capas de prueba: integración HTTP + verificación de invariantes con consultas SQL en la misma base.

### D-09 — Compatibilidad y regresión

- Se conservan 201/404/409/422, los mensajes propios y las rutas del TP que la matriz no reemplaza.
- Cambios de contrato esperados: `stock` → `stock_inicial` en `POST /libros`; `stock` fuera de `PATCH /libros/{id}`; `GET /ventas/{id}` ya no exige rol; se agregan `/mis-ventas`, `DELETE`, `reponer` y `movimientos`.
- Los `.http` de C-01..C-12 que usen `stock` se actualizarán en C-14; esta suite pytest es la validación de C-13.

## Riesgos

- **Trigger de solo agregado**: el historial no se puede corregir con UPDATE/DELETE; los tests solo insertan movimientos.
- **TRUNCATE y trigger**: el trigger es `BEFORE UPDATE OR DELETE FOR EACH ROW`; `TRUNCATE` no lo dispara, por eso el aislamiento entre tests es seguro.
- **Orden de autorización**: se carga la venta (404) y después se decide el permiso (403); un cliente no puede distinguir ventas ajenas de inexistentes por el código (ambas 403/404 según el caso).
