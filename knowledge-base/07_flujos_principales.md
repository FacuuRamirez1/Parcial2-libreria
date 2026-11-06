# Flujos Principales

## Flujo 1: Registrar una venta

**Disparador**: `POST /ventas/` con `cliente_id` y `renglones`.
**Actor**: operador.

**Pasos**:
1. El router valida el DTO `VentaCreate` (al menos un renglón, sin `libro_id` repetido, `cantidad > 0`). Si falla: 422 sin ejecutar el service.
2. El service lee de la base los libros de los renglones para copiar su `precio` a `precio_unitario` (el precio nunca viaja en el DTO).
3. Calcula `total = Σ cantidad × precio_unitario` con `Decimal`.
4. Crea la `Venta` con sus `RenglonVenta` en `venta.renglones` (composición) y hace commit.
5. Si la base rechaza (FK de cliente o libro inexistente): se traduce el `IntegrityError` y responde 409 con mensaje propio.
6. Recarga la venta con cliente y renglones usando carga anticipada y responde 201.
7. Se agenda con `BackgroundTasks` el aviso del comprobante (`asyncio.sleep(0.5)` + log), que corre después de enviar la respuesta.

```
Operador → router → service → BD (lee libros)
                        └──► BD (inserta venta + renglones)
                        ◄── venta con cliente y renglones (carga anticipada)
router ◄── 201          └──► BackgroundTask: aviso de comprobante
```

**Casos de error**:
- Libro repetido o sin renglones → 422.
- Cliente o libro inexistente → 409 con mensaje propio, sin texto de la base.

## Flujo 2: Alta de libro con autores

**Disparador**: `POST /libros/` con `editorial_id`, `genero_id`, `autores` (`autor_id`, `rol`, `orden`).

**Pasos**:
1. El DTO valida precio > 0, stock ≥ 0, `rol` permitido y `orden ≥ 1`.
2. El service crea el `Libro` y sus `LibroAutor` y hace commit **sin consultar antes** si los ids existen.
3. Si la base rechaza el FK, el ISBN repetido o un CHECK: se traduce el `IntegrityError` a 409 con mensaje propio.
4. Se devuelve 201 con el detalle (editorial, género, autores) cargado en la misma consulta.

**Casos de error**:
- ISBN repetido → 409.
- Editorial o autor inexistente → 409 con mensaje propio.

## Flujo 3: Detalle de libro o de venta sin N+1

**Disparador**: `GET /libros/{id}` o `GET /ventas/{id}`.

**Pasos**:
1. El service arma **una consulta** con `joinedload` (editorial, género, cliente) y `selectinload` (autorías con su autor, renglones con su libro).
2. Devuelve el DTO `Read`. El número de consultas es fijo, con uno o con muchos autores o renglones (evidencia C-07).

**Casos de error**: id inexistente → 404; id no entero → 422.

## Flujo 4: Perfil único del cliente

**Disparador**: `POST /clientes/{id}/perfil`.

**Pasos**: se inserta `PerfilCliente` con `cliente_id`. Si ya existía uno, el UNIQUE de la base lo rechaza y se responde 409 (RN-09).

## Flujo 5: Búsqueda de libros por título

**Disparador**: `GET /libros/?titulo=...&genero_id=...&limit=...&offset=...`.

**Pasos**: el texto se pasa como parámetro ligado (`ilike`) y nunca se concatena al SQL. Con `' OR '1'='1` la respuesta es 200 con lista vacía (C-08).

## Flujo 6: Esquema desde cero

**Disparador**: base vacía.

**Pasos**: `alembic upgrade head` aplica la migración 1 (todo menos `genero`) y la 2 (`genero` y `libro.genero_id`). `downgrade -1` seguido de `upgrade head` debe funcionar. Después se ejecuta el script de datos iniciales.
