# Modelo de Datos

Los nombres de tablas y columnas son **obligatorios** (los casos de prueba y la corrección los usan). Se pueden agregar columnas, pero no quitar ni renombrar las indicadas. Dinero: `Decimal` / `NUMERIC`, nunca `float`. Fechas nuevas: `timestamptz`. Cada FK nueva lleva índice (PostgreSQL no lo crea solo). La navegación se declara en los dos extremos.

> **TP caps 1-4 (implementado)**: 9 tablas. **Parcial (pendiente)**: +5 tablas nuevas, cambios a `cliente` y `libro`, 2 migraciones más. Las tablas `editorial`, `genero`, `autor`, `libro_autor`, `perfil_cliente` (y `venta`, `renglon_venta`) **no cambian**.

## Dominios

- **Catálogo:** editorial, genero, autor, libro (cambia), libro_autor, **movimiento_stock** (nuevo, vive en el módulo `libros`).
- **Clientes:** cliente (cambia), perfil_cliente.
- **Ventas:** venta, renglon_venta.
- **Acceso (nuevo, módulo `usuarios`):** usuario, asignacion_rol, intento_acceso, evento_seguridad.

## ERD

```
editorial 1 ──< libro >── 0..1 genero          (agregación; género opcional)
libro 1 ──< libro_autor >── 1 autor             (muchos a muchos con datos: rol, orden)
cliente 1 ── 0..1 perfil_cliente                (uno a uno; composición)
cliente 1 ──< venta                             (asociación)
venta 1 ──< renglon_venta                       (composición)
renglon_venta >── 1 libro                       (asociación)
--- Parcial ---
usuario 1 ── 0..1 cliente                       (cliente.usuario_id UNIQUE, nulo permitido)
usuario 1 ──< asignacion_rol                    (roles con vigencia; asignacion_rol.otorgada_por → usuario, nulo)
libro 1 ──< movimiento_stock >── 0..1 venta     (venta_id nulo: alta/reposición)
usuario 1 ──< movimiento_stock                   (quién lo hizo)
intento_acceso, evento_seguridad                 (sin relación con ninguna tabla)
```

| Relación | Tipo | Alcance |
|---|---|---|
| Libro–Editorial | Agregación | TP |
| Libro–Género | Agregación opcional (`genero_id` nulo) | TP |
| Libro–Autor | M:N con datos (`LibroAutor`: rol, orden) | TP |
| Cliente–Perfil | Uno a uno (`perfil_cliente.cliente_id` UNIQUE); `Cliente.perfil` objeto | TP |
| Venta–Cliente | Asociación | TP |
| Venta–Renglón | Composición | TP |
| Renglón–Libro | Asociación (el libro puede estar dado de baja y igual se muestra) | TP + Parcial |
| Cliente–Usuario | Uno a uno opcional; `Cliente.usuario` devuelve un objeto, no una lista | Parcial |
| Usuario–AsignaciónRol | Uno a muchos | Parcial |
| Libro–MovimientoStock / Venta–MovimientoStock | Uno a muchos (movimiento ligado a venta o no) | Parcial |

## Entidades

### editorial / genero / autor — sin cambios (TP)
- `editorial`: `id`, `nombre` (UNIQUE), `pais`. `genero`: `id`, `nombre` (UNIQUE). `autor`: `id`, `nombre`, `nacionalidad`.

### libro (cambia)
- TP: `id`, `isbn`, `titulo`, `precio` NUMERIC(10,2), `stock`, `editorial_id` (FK), `genero_id` (FK nula). `isbn` UNIQUE; CHECK `precio > 0`; CHECK `stock >= 0`; índices en FKs.
- **Parcial**: se agrega `borrado_en` (`timestamptz`, nulo). El `UNIQUE` del ISBN se **reemplaza** por un **índice único parcial** `(isbn) WHERE borrado_en IS NULL` (`postgresql_where`): el ISBN es único solo entre los vigentes y se puede volver a cargar uno dado de baja. Siguen los CHECK de precio y stock.
- `libro.stock` = suma de `movimiento_stock.cantidad` del libro (invariante verificada tras cada caso de venta). Se escribe en un único punto del código.

### libro_autor — sin cambios (TP)
- PK (`libro_id`, `autor_id`), `rol` ∈ (`autor`, `coautor`, `traductor`, `ilustrador`), `orden >= 1`; índice en `autor_id`.

### cliente (cambia)
- TP: `id`, `nombre`, `email` UNIQUE.
- **Parcial**: se agrega `usuario_id` (FK a `usuario`, nulo, **UNIQUE**; un cliente puede o no tener acceso web). `email` sigue UNIQUE. Índice de la FK cubierto por el UNIQUE.

### perfil_cliente — sin cambios (TP)
- `id`, `cliente_id` UNIQUE, `telefono`, `direccion`.

### venta / renglon_venta — sin cambios de esquema (TP)
- `venta`: `id`, `cliente_id`, `fecha` (tz), `total` NUMERIC(12,2) CHECK `>= 0`. `renglon_venta`: `id`, `venta_id`, `libro_id`, `cantidad > 0`, `precio_unitario > 0` NUMERIC(10,2).
- Parcial: el comportamiento cambia (descuenta stock y deja un movimiento por renglón).

### usuario (nuevo)
- `id`, `email`, `nombre`, `password_hash`, `activo`, `debe_cambiar_password`.
- Constraint: `email` UNIQUE. **No tiene columna `rol`.** Ninguna respuesta incluye `password_hash`.

### asignacion_rol (nuevo)
- `id`, `usuario_id` (FK), `rol`, `desde`, `vence_en` (nulo), `revocada_en` (nulo), `otorgada_por` (nulo).
- CHECK `rol IN ('ADMIN','VENDEDOR','CLIENTE')`.
- **Índice único parcial** `(usuario_id, rol) WHERE revocada_en IS NULL`: a lo sumo una asignación abierta por rol (RN-03).
- Vigente = `revocada_en IS NULL` y (`vence_en IS NULL` o `vence_en` futuro). La fila nunca se borra. Índice en FKs (`usuario_id`, `otorgada_por`).

### intento_acceso (nuevo)
- `id`, `cuando`, `email`, `ip`, `exito`. Índice `(email, ip, cuando)`. Sin otras restricciones ni FK. Se escribe en sesión y transacción propias (siempre confirmadas).

### evento_seguridad (nuevo)
- `id`, `cuando`, `actor` (**texto**, no FK: puede ser `SISTEMA`), `accion`. Sin restricciones extra ni relaciones.

### movimiento_stock (nuevo, módulo `libros`)
- `id`, `libro_id` (FK), `venta_id` (FK, nulo), `usuario_id` (FK), `cantidad`, `motivo`, `cuando`.
- CHECK `cantidad <> 0`. **Solo agregado**: un trigger rechaza cualquier UPDATE o DELETE (migración 0004 a mano). Índices en las tres FK. Los errores se compensan con otro movimiento.

## Migraciones

| # | Contenido | Origen | Alcance |
|---|---|---|---|
| 0001 | Todo el TP menos `genero` | autogenerada | TP (implementado) |
| 0002 | `genero` + `libro.genero_id` | autogenerada | TP (implementado) |
| 0003 | Tablas de acceso (`usuario`, `asignacion_rol`, `intento_acceso`, `evento_seguridad`), `movimiento_stock`, cambios en `cliente` (`usuario_id`) y `libro` (`borrado_en`, índice único parcial del ISBN en lugar del UNIQUE) | `--autogenerate`, leída antes de aplicar, con comentario | Parcial (C-10) |
| 0004 | Función + **trigger** de solo agregado sobre `movimiento_stock` (UPDATE/DELETE → excepción) | a mano (la comparación automática no ve funciones ni triggers), con comentario | Parcial (C-10) |

Reglas: sin `create_all`; cada migración nueva lleva un comentario que diga que se leyó (y, si se corrigió lo generado, por qué). `upgrade head` sobre base vacía, `downgrade base`, `upgrade head` deben funcionar. Con el UNIQUE→índice parcial del ISBN, revisar que el autogenerate lo detecte; si no, corregir a mano. El downgrade de 0004 elimina trigger y función.

> Nota con datos existentes: pasar `libro.stock` a "suma de movimientos" exige que los libros ya cargados tengan su movimiento "Stock inicial" (resuelve el seed; ver IN-05).

## Navegación

FK con navegación en los dos extremos (`Relationship(back_populates=...)`) y toda relación leída se precarga en el repositorio (`joinedload`/`selectinload`). `Cliente.usuario` y `Cliente.perfil` devuelven un objeto.

## Seed data inicial

### TP (implementado) — `scripts/seed.py`
Editoriales, géneros, autores, 5 libros, clientes (con y sin perfil) y una venta. Ver C-03 archivado.

### Parcial (pendiente) — `seed.py`
Vacía las tablas y carga como mínimo (los casos de prueba los usan). Las contraseñas son de mentira y viven solo en ese archivo. Es parte de la puesta en marcha, no un extra.

| Qué | Datos |
|---|---|
| Usuarios | `admin@example.com` y `admin2@example.com` (ADMIN), `vendedor@example.com` (VENDEDOR), `ana@example.com` (CLIENTE), `nuevo@example.com` (VENDEDOR, con `debe_cambiar_password = true`) |
| Editoriales, géneros, autores | Los del TP: 3, 3 y 6 |
| Libros | Los cinco del TP con su stock actual: Rayuela 10, Antología de la literatura fantástica 5, Ficciones 8, Respiración artificial 3, Bestiario 1 |
| Clientes | Lucía Fernández (con perfil) y Tomás Ríos, sin usuario; Ana Paz, con el usuario `ana@example.com` |
| Venta | La 1, de Lucía, registrada por `vendedor@example.com`: 1 Rayuela y 2 Ficciones, total 69000.00 |
| Movimientos | Un "Stock inicial" por libro. Rayuela y Ficciones se cargan con 11 y 10 ejemplares; la venta 1 deja dos salidas (−1 y −2), de modo que stock = suma de movimientos en los cinco libros |
| Historial de seguridad | Una línea con actor `SISTEMA`: "Carga de los datos iniciales" |

Para el despliegue (D-03) el "comando de datos iniciales" es el del README del **TP** (`docker exec libreria …`), no el seed del Parcial.
