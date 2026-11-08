# Modelo de Datos

Los nombres de tablas y columnas son **obligatorios** (los casos de prueba y la corrección los usan). Se pueden agregar columnas, pero no quitar ni renombrar las indicadas. El dinero es `Decimal`, nunca `float`.

## Dominios

- **Catálogo:** editorial, genero, autor, libro, libro_autor.
- **Clientes:** cliente, perfil_cliente.
- **Ventas:** venta, renglon_venta.

## ERD

```
editorial 1 ──< libro >── 0..1 genero          (agregación; género opcional)
libro 1 ──< libro_autor >── 1 autor             (muchos a muchos con datos: rol, orden)
cliente 1 ── 0..1 perfil_cliente                (uno a uno; composición)
cliente 1 ──< venta                             (asociación)
venta 1 ──< renglon_venta                       (composición)
renglon_venta >── 1 libro                       (asociación)
```

| Relación | Entre | Tipo | Por qué |
|---|---|---|---|
| Libro–Editorial | libro, editorial | Agregación | El libro incorpora una editorial existente; viaja su id y la comparten muchos libros |
| Libro–Género | libro, genero | Agregación opcional | `genero_id` admite NULL |
| Libro–Autor | libro, autor | Muchos a muchos con datos | `LibroAutor` es entidad propia con rol y orden; se navega `libro.autorias[i].autor` |
| Cliente–Perfil | cliente, perfil_cliente | Uno a uno | `perfil_cliente.cliente_id` UNIQUE; `Cliente.perfil` devuelve un objeto, no una lista |
| Venta–Cliente | venta, cliente | Asociación | La venta conoce al cliente; ninguno es parte del otro |
| Venta–Renglón | venta, renglon_venta | Composición | Un renglón no existe sin su venta; se crea con ella |
| Renglón–Libro | renglon_venta, libro | Asociación | El renglón nombra un libro existente |

## Entidades

### editorial
- `id`, `nombre`, `pais`.
- Constraint: `nombre` UNIQUE.

### genero
- `id`, `nombre`.
- Constraint: `nombre` UNIQUE.

### autor
- `id`, `nombre`, `nacionalidad`.
- Sin restricciones extra.

### libro
- `id`, `isbn`, `titulo`, `precio` NUMERIC(10,2), `stock`, `editorial_id` (FK), `genero_id` (FK, nulo permitido).
- Constraints: `isbn` UNIQUE; CHECK `precio > 0`; CHECK `stock >= 0`.
- Índices: uno por cada clave foránea (`editorial_id`, `genero_id`).

### libro_autor
- `libro_id`, `autor_id`, `rol`, `orden`.
- PK compuesta (`libro_id`, `autor_id`).
- Constraints: CHECK `orden >= 1`; CHECK `rol` en (`autor`, `coautor`, `traductor`, `ilustrador`).
- Vive en el módulo `libros`. Índice en `autor_id` (el de `libro_id` lo cubre la PK).

### cliente
- `id`, `nombre`, `email`.
- Constraint: `email` UNIQUE.

### perfil_cliente
- `id`, `cliente_id` (FK), `telefono`, `direccion`.
- Constraint: `cliente_id` UNIQUE (garantiza el uno a uno).
- Vive en el módulo `clientes`.

### venta
- `id`, `cliente_id` (FK), `fecha` (con zona horaria), `total` NUMERIC(12,2).
- Constraint: CHECK `total >= 0`. Índice en `cliente_id`.

### renglon_venta
- `id`, `venta_id` (FK), `libro_id` (FK), `cantidad`, `precio_unitario` NUMERIC(10,2).
- Constraints: CHECK `cantidad > 0`; CHECK `precio_unitario > 0`. Índices en `venta_id` y `libro_id`.
- Vive en el módulo `ventas`.

## Navegación

Cada clave foránea lleva navegación en **los dos extremos** con `Relationship(back_populates=...)` y un índice (PostgreSQL no lo crea solo). Toda relación que se lee se precarga en la consulta (ver `05_reglas_de_negocio.md`, RN-12 y NF-04).

## Seed data inicial

Un script Python asincrónico deja la base en un estado inicial conocido (casos C-01 a C-08): al menos editoriales, géneros, autores, libros con uno y varios autores, clientes (alguno con perfil y alguno sin) y una venta. Ejemplos de la consigna: "Rayuela", "Respiración artificial", "Los que aman, odian", clientes como "Tomás Ríos".
