# Trabajo Práctico — Librería: catálogo, clientes y ventas

Programación III (UTN, TUP a distancia) · Comisión 4
Integrantes: Facundo Deseff, Facundo Ramírez, Santino Godoy y Matías Vargas
Repositorio: <https://github.com/FacuuRamirez1/TP_Backend>

API REST asincrónica para una librería: editoriales, géneros, autores, libros, clientes, perfiles y ventas. Construida con **FastAPI + SQLModel + SQLAlchemy asincrónico + PostgreSQL**, con migraciones **Alembic** y casos de prueba en archivos `.http`.

El esquema se crea **exclusivamente** con las migraciones de Alembic (no hay `create_all`). El archivo `.env` contiene la configuración local y no se versiona; se parte de [env.example](./env.example).

## Requisitos previos

- Python 3.12 o superior.
- PostgreSQL 16 o superior (probado con PostgreSQL 17).
- Una base PostgreSQL vacía llamada `libreria`.
- Git. En Windows, PowerShell.

## 1. Clonar y crear la base

```powershell
git clone https://github.com/FacuuRamirez1/TP_Backend
cd TP_Backend
createdb -U postgres libreria
```

Si no tenés `createdb` en el PATH, creá la base desde `psql`:

```sql
CREATE DATABASE libreria;
```

## 2. Entorno virtual y dependencias

Windows (PowerShell):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Si PowerShell impide activar scripts, ejecutá `Set-ExecutionPolicy -Scope Process Bypass` en esa consola y volvé a activar el entorno.

Linux / macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3. Variables de entorno

Copiá `env.example` a `.env` y ajustá los datos de tu PostgreSQL:

```powershell
Copy-Item env.example .env
```

```dotenv
DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/libreria
SQL_ECHO=false
```

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `DATABASE_URL` | Sí | URL de PostgreSQL con el driver asincrónico `postgresql+asyncpg`. |
| `SQL_ECHO` | No | `true`, `1`, `yes` u `on` muestran el SQL en consola (se usa para el caso C-07). |

Nunca escribas credenciales en el código, en `alembic.ini` ni en archivos versionados.

## 4. Crear el esquema con Alembic

```powershell
alembic upgrade head
```

La carpeta [migrations/](./migrations/) contiene la configuración asincrónica de Alembic y **dos** revisiones generadas con `--autogenerate`:

1. `0001`: crea todas las tablas del dominio **menos `genero`** (y sin `libro.genero_id`).
2. `0002` (cabeza actual): crea `genero` y agrega `libro.genero_id` (nulo, con índice y FK nombrada).

Cada revisión se leyó antes de aplicarla y lleva un comentario en su docstring con lo revisado. No hizo falta corregir el SQL generado, salvo `import sqlmodel` en el template `script.py.mako`, que faltaba para las columnas de texto de SQLModel.

Para comprobar el ciclo completo:

```powershell
alembic downgrade -1
alembic upgrade head
alembic check
```

## 5. Datos iniciales

```powershell
python scripts/seed.py
```

El script es asincrónico e idempotente: si ya hay libros, no vuelve a cargar nada. Deja la base en un estado conocido: 3 editoriales, 3 géneros, 6 autores, 4 libros (el libro 3 con tres coautores), 2 clientes (el 1, Ana Pérez, con perfil; el 2, Tomás Ríos, sin perfil) y una venta (id 1) con dos renglones. Los libros 1 y 4 cuestan `25000.00` y `27000.00`, como en el ejemplo de la consigna.

## 6. Arrancar la API

```powershell
uvicorn app.main:app --reload
```

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Salud: <http://127.0.0.1:8000/health/live> y `/health/ready`

## 7. Endpoints

Todos los listados devuelven una **lista simple** y se paginan con `limit` (1 a 100, por defecto 20) y `offset` (desde 0). Un valor fuera de rango responde `422` sin ejecutar el handler. Los recursos inexistentes responden `404`, los conflictos de integridad `409` con un mensaje propio (nunca texto de la base) y los contratos incumplidos `422`.

### Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health/live` | `{"estado": "vivo"}`; no toca la base. |
| GET | `/health/ready` | Ejecuta `SELECT 1` y devuelve el estado de la base. |

### Catálogo

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/editoriales/` | Alta (`201`, `409`, `422`). |
| GET | `/editoriales/` | Listado paginado. |
| GET | `/editoriales/{id}` | Detalle. |
| PATCH | `/editoriales/{id}` | Actualización parcial (`exclude_unset`). |
| GET | `/editoriales/{id}/libros` | Libros de la editorial (`404` si no existe). |
| POST | `/generos/` | Alta (`201`, `409`). |
| GET | `/generos/` | Listado paginado. |
| GET | `/generos/{id}` | Detalle. |
| PATCH | `/generos/{id}` | Actualización parcial. |
| GET | `/generos/{id}/libros` | Libros del género (`404` si no existe). |
| POST | `/autores/` | Alta (`201`, `422`). |
| GET | `/autores/` | Listado paginado. |
| GET | `/autores/{id}` | Detalle. |
| PATCH | `/autores/{id}` | Actualización parcial. |
| GET | `/autores/{id}/libros` | Libros del autor con el `rol` y el `orden` de cada autoría. |

### Libros

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/libros/` | Alta con `editorial_id`, `genero_id` (opcional) y `autores` (`autor_id`, `rol`, `orden`). Responde el detalle (`201`, `409`, `422`). |
| GET | `/libros/?limit=&offset=&titulo=&genero_id=` | Listado con editorial y género; `titulo` busca por parte del título sin distinguir mayúsculas, con parámetro ligado. |
| GET | `/libros/{id}` | Detalle con editorial, género y autores. |
| PATCH | `/libros/{id}` | Actualización parcial (ISBN, título, precio, stock, editorial, género). Responde el detalle. |

### Clientes y perfil

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/clientes/` | Alta (`201`, `409` por email repetido, `422`). |
| GET | `/clientes/` | Listado paginado. |
| GET | `/clientes/{id}` | Cliente con su perfil (objeto o `null`). |
| PATCH | `/clientes/{id}` | Actualización parcial; responde el cliente con su perfil. |
| POST | `/clientes/{id}/perfil` | Alta del perfil (`201`; `409` si ya tiene uno; `404` si el cliente no existe). |
| GET | `/clientes/{id}/ventas` | Ventas del cliente, con cliente y renglones. |

### Ventas

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/ventas/` | Alta con `cliente_id` y `renglones` (`libro_id`, `cantidad`). El servidor copia el precio de cada libro, calcula el total y pone la fecha (`201`, `409`, `422`). |
| GET | `/ventas/` | Listado paginado, con cliente y renglones. |
| GET | `/ventas/{id}` | Detalle con cliente y renglones (`titulo`, `precio_unitario`, `subtotal`). |

Las ventas no tienen `PATCH` ni `DELETE`, y no existe un alta de renglones por separado. Un cliente o libro inexistente responde `409` y no deja filas nuevas.

## 8. Tarea en segundo plano

Al crear una venta, `POST /ventas/` encola con `BackgroundTasks` el aviso `enviar_aviso_comprobante(venta_id, total)`. La corrutina espera `await asyncio.sleep(0.5)` sin bloquear el event loop y registra en el log:

```text
INFO:     app.modules.ventas.service: Aviso de comprobante enviado: venta=2 total=77000.00
```

La respuesta `201` se envía antes de que el aviso termine; un fallo del aviso no revierte la venta. Mientras el aviso duerme, el servidor sigue atendiendo otras peticiones (por ejemplo `GET /health/live`). `app/main.py` configura el logger `app` en nivel INFO para que el mensaje aparezca en la consola de uvicorn.

## 9. Casos de prueba C-01 a C-08

La carpeta [test/](./test/) contiene los archivos `.http` (extensión REST Client de VS Code), cada uno con su respuesta esperada en un comentario. Requieren la base migrada y con `python scripts/seed.py` ejecutado; **C-07 usa la venta que crea C-06**, así que conviene correrlos en orden.

| Caso | Qué se demuestra | Archivo | Resultado esperado |
|------|------------------|---------|--------------------|
| C-01 | Parámetro de ruta no entero | `test/C-01-validacion-ruta.http` | `422`, sin ejecutar el handler |
| C-02 | ISBN o email repetido | `test/C-02-unicidad.http` | `409` con mensaje propio |
| C-03 | Segundo perfil del mismo cliente | `test/C-03-perfil-unico.http` | `409` |
| C-04 | Libro con editorial o autor inexistente | `test/C-04-fk-libro.http` | `409` con mensaje propio |
| C-05 | Venta con libro o cliente inexistente | `test/C-05-venta-invalida.http` | `409` |
| C-06 | Venta válida con dos renglones | `test/C-06-venta-valida.http` | `201`, precios copiados y total `77000.00` |
| C-07 | Detalle de un libro y de una venta | `test/C-07-detalles.http` | Cantidad fija de consultas en la consola |
| C-08 | Búsqueda con el texto `' OR '1'='1` | `test/C-08-busqueda-segura.http` | `200` con lista vacía |

`test/extras-endpoints.http` agrupa los endpoints de relación y el `PATCH` parcial.

## Evidencia del caso C-07

Para ver las consultas se arrancó el servidor con `SQL_ECHO=true` (base migrada con `alembic upgrade head`, `python scripts/seed.py` y la venta de C-06 creada). Las capturas literales de la consola, recortadas al ancho de la página, son estas.

### 1. Detalle de un libro: `GET /libros/1` (un autor) y `GET /libros/3` (tres autores)

Las dos peticiones emiten **las mismas 2 consultas**: la primera trae el libro con su editorial y su género (`joinedload`, relaciones a uno) y la segunda las autorías con su autor (`selectinload` + `joinedload`).

```text
INFO sqlalchemy.engine.Engine SELECT libro.id, libro.isbn, libro.titulo, libro.precio, libro.stock, libro.editorial_id, libro.genero_id, editorial_1.id AS id_1, editorial_1.nombre, editorial_1.pais, genero_1.id AS id_2, genero_1.nombre
FROM libro LEFT OUTER JOIN editorial AS editorial_1 ON editorial_1.id = libro.editorial_id LEFT OUTER JOIN genero AS genero_1 ON genero_1.id = libro.genero_id
WHERE libro.id = $1::INTEGER
INFO sqlalchemy.engine.Engine [generated in 0.00061s] (1,)
INFO sqlalchemy.engine.Engine SELECT libro_autor.libro_id AS libro_autor_libro_id, libro_autor.autor_id AS libro_autor_autor_id, libro_autor.rol AS libro_autor_rol, libro_autor.orden AS libro_autor_orden, autor_1.id AS autor_1_id, ...
FROM libro_autor LEFT OUTER JOIN autor AS autor_1 ON autor_1.id = libro_autor.autor_id
WHERE libro_autor.libro_id IN ($1::INTEGER) ORDER BY libro_autor.orden
INFO sqlalchemy.engine.Engine [generated in 0.00054s] (1,)
```

`GET /libros/3` repite exactamente esas dos sentencias con el parámetro `(3,)` aunque el libro tiene tres autores.

### 2. Detalle de una venta: `GET /ventas/1` y `GET /ventas/2` (dos renglones cada una)

Ambas peticiones emiten **2 consultas**: la venta con su cliente (`joinedload`) y los renglones con su libro (`selectinload` + `joinedload`).

```text
INFO sqlalchemy.engine.Engine SELECT venta.id, venta.cliente_id, venta.fecha, venta.total, cliente_1.id AS id_1, cliente_1.nombre, cliente_1.email
FROM venta LEFT OUTER JOIN cliente AS cliente_1 ON cliente_1.id = venta.cliente_id
WHERE venta.id = $1::INTEGER
INFO sqlalchemy.engine.Engine [cached since 7.534s ago] (1,)
INFO sqlalchemy.engine.Engine SELECT renglon_venta.venta_id AS renglon_venta_venta_id, renglon_venta.id AS renglon_venta_id, renglon_venta.libro_id AS renglon_venta_libro_id, ...
FROM renglon_venta LEFT OUTER JOIN libro AS libro_1 ON libro_1.id = renglon_venta.libro_id
WHERE renglon_venta.venta_id IN ($1::INTEGER) ORDER BY renglon_venta.id
INFO sqlalchemy.engine.Engine [cached since 7.525s ago] (1,)
```

La cantidad no crece con los renglones: es la misma con uno o con varios autores o renglones (ver `test/C-07-detalles.http`).

## 10. Pruebas

Las pruebas son **solo archivos `.http`** en `test/` (casos C-01 a C-08 más `extras-endpoints.http`), con la respuesta esperada de cada petición en un comentario. Se ejecutan con la extensión REST Client de VS Code contra la API levantada y la base cargada con `python scripts/seed.py`.

## 11. Estructura

```text
app/
  main.py               aplicación, lifespan y registro de routers
  core/                 config (DATABASE_URL), motor/sesiones (get_session), errores, paginación
  modules/
    health/             liveness y readiness
    editoriales/        models, schemas, service, router
    generos/
    autores/
    libros/             libro y LibroAutor (objeto de asociación)
    clientes/           cliente y PerfilCliente
    ventas/             venta, RenglonVenta y aviso en segundo plano
migrations/             Alembic (0001 todo menos genero, 0002 genero y libro.genero_id)
scripts/seed.py         datos iniciales idempotentes
test/                   casos C-01 a C-08 (.http)
```

## 12. Reglas de implementación

- Esquema solo por Alembic; nunca `create_all`.
- La lógica vive en el `service` de cada módulo, que recibe la sesión como parámetro (sin repositorios ni Unit of Work).
- Dinero con `Decimal` y `NUMERIC`, nunca `float`.
- No se pre-consulta unicidad ni existencia de ids en las altas: se escribe y la restricción responde `409`.
- Los mensajes de error no filtran tablas, restricciones ni trazas internas.
- Sin carga perezosa (`lazy="raise"`): `joinedload` para relaciones a uno y `selectinload` para colecciones, declarados en la misma consulta.
- Handlers `async def`; sin llamadas bloqueantes ni SQL concatenado con datos del usuario.
- DTOs de entrada con `extra="forbid"`; los de alta no llevan `id`.

## 13. Problemas frecuentes

- **`Falta la variable DATABASE_URL`**: no existe `.env` o la variable no está definida en el entorno.
- **`DATABASE_URL debe usar el driver asincrónico postgresql+asyncpg`**: corregí el prefijo de la URL.
- **`alembic upgrade head` falla por conexión**: revisá usuario, clave, puerto y que la base exista.
- **Un `409` al crear**: el mensaje indica duplicado o referencia inválida; no se expone el detalle interno de PostgreSQL.
