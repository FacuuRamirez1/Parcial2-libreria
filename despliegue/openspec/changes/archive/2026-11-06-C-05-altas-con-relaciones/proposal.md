# Proposal

## Why

C-04 dejó los contratos, los endpoints CRUD y el handler global de `IntegrityError`, pero las altas con relaciones del Ejercicio 5 (20 pts; US-006, US-007, US-008) siguen incompletas: `POST /libros/` no acepta `autores`, `POST /ventas/` no confirma la transacción (la venta no persiste) y devuelve 400/409 donde la consigna pide 422, y la respuesta de venta no expone `titulo`. Sin este change, los casos C-05 de la consigna no se cumplen.

## What Changes

- `POST /libros/` acepta `autores[{autor_id, rol, orden}]`, crea `Libro` + `LibroAutor` en una única transacción y responde 201. Sin consultas previas de existencia: ISBN, FK o CHECK rechazados por la base se traducen a 409 con mensaje propio.
- Contrato de alta de libro: `precio > 0`, `stock_inicial >= 0`, `rol` dentro de `autor`, `coautor`, `traductor`, `ilustrador`, `orden >= 1` (422 si no se cumple); `genero_id` pasa a ser **obligatorio en el DTO** (aunque la columna admita NULL) y debe referenciar un género existente.
- `POST /clientes/{id}/perfil` responde 201; un segundo perfil responde 409 (RN-09) y un cliente inexistente también responde **409**, por consistencia con el resto de los altas con FK. No se pre-consulta el id: se distinguen UNIQUE y FK por el SQLSTATE del error de la base y se responde con un mensaje propio distinto en cada caso.
- `POST /ventas/` valida en el DTO al menos un renglón y la ausencia de `libro_id` repetido, ambos con **422** (hoy 400 y 409; **BREAKING** respecto del contrato previo). `cantidad > 0` se mantiene en 422.
- `POST /ventas/` lee los precios de los libros, copia `precio_unitario`, calcula `total` y `subtotal` con `Decimal`, usa la `fecha` del servidor y **confirma la transacción** para que la venta y sus renglones persistan. Cliente o libro inexistente responden 409 con mensaje propio.
- `RenglonVentaRead` incorpora `titulo`; la respuesta 201 y las lecturas de ventas incluyen `titulo`, `precio_unitario` y `subtotal`.
- Se incorpora la infraestructura de tests automatizados que hoy no existe: `pytest`, `pytest-asyncio` y `httpx` (con `ASGITransport`) en `requirements-dev.txt`, más `conftest.py` con app y base de prueba. Los archivos `test/*.http` se mantienen como verificación manual de la consigna.
- Fuera de alcance: optimización y conteo de consultas N+1 (C-06), `BackgroundTasks` del comprobante (C-07), autenticación/RBAC, descuento de stock al vender (SU-01) y cualquier cambio de esquema (no hay migración nueva).

## Capabilities

### New Capabilities

- `altas-libros-autores`: alta de libro con editorial, género obligatorio en el contrato y autores con rol y orden; validaciones de contrato y errores 409/422.
- `altas-perfil-cliente`: alta del perfil único de un cliente existente, con 409 tanto para cliente inexistente como para perfil duplicado (mensajes propios distintos).
- `altas-ventas`: alta de venta con renglones, validación 422, copia de precios, total calculado por el servidor, fecha del servidor y respuesta con `titulo`.
- `transacciones-venta`: atomicidad y persistencia del alta de venta (y de sus renglones) en una única transacción, con rollback completo ante rechazo de la base.

### Modified Capabilities

Ninguna. Los specs de C-04 (`contratos-*`, `endpoints-crud`, `handler-integridad-global`) son deltas aún no archivados y no existen todavía en `openspec/specs/`; C-05 introduce capacidades nuevas en lugar de modificar los specs de datos (`catalog-data`, `customer-data`, `sales-data`), cuyo esquema no cambia.

## Impact

- **Código**: `app/modules/libros/{schemas,service}.py` (contrato y alta transaccional con autores), `app/modules/clientes/{schemas,service}.py` (409 del perfil), `app/modules/ventas/{schemas,service}.py` (validación 422, respuesta con `titulo`, commit y precarga de libros). `app/core/errors.py` y `app/core/unit_of_work.py` se reutilizan; no se modifican tablas.
- **API**: `POST /libros/`, `POST /clientes/{id}/perfil` y `POST /ventas/` cambian contrato o códigos como se detalla arriba; `GET /ventas/` y `GET /ventas/{id}` incorporan `titulo` en cada renglón.
- **Dependencias**: nuevas dependencias **solo de desarrollo** (`pytest`, `pytest-asyncio`, `httpx`); `requirements.txt` de producción no cambia.
- **Base de datos**: sin migraciones; se usan las tablas `libro_autor`, `perfil_cliente`, `venta` y `renglon_venta` ya existentes.
- **Changes posteriores**: C-06 parte de las precargas y del `titulo` ya expuestos por la respuesta de venta; C-07 agrega el `BackgroundTasks` sobre el alta de venta ya transaccional.
