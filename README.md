# Librería — API (Parcial 2)

API REST para la gestión de una librería: editoriales, géneros, autores, libros, clientes, perfiles y ventas. Construida con **FastAPI + SQLModel + SQLAlchemy asincrónico + PostgreSQL**, con migraciones **Alembic** y pruebas **pytest**.

## Requisitos

- Python 3.12 o superior.
- PostgreSQL 16 o superior (probado con PostgreSQL 17).
- Git.
- En Windows, PowerShell 5.1 o superior.

## 1. Clonar y crear la base

```powershell
git clone <url-del-repo>
cd Tp_Libreria
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
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Linux / macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Para ejecutar la suite de pruebas, instalá además las dependencias de desarrollo:

```powershell
pip install -r requirements-dev.txt
```

## 3. Variables de entorno

Copiá `env.example` a `.env` (el `.env` **no se versiona**) y ajustá los datos de tu PostgreSQL:

```powershell
Copy-Item env.example .env
```

```dotenv
DATABASE_URL=postgresql+asyncpg://postgres:tu_clave@localhost:5432/libreria
SQL_ECHO=false
```

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `DATABASE_URL` | Sí | URL de PostgreSQL con el driver asincrónico `postgresql+asyncpg`. |
| `SQL_ECHO` | No | `true`, `1`, `yes` u `on` muestran el SQL en consola. |

Nunca escribas credenciales en el código, en `alembic.ini` ni en archivos versionados.

## 4. Crear el esquema con Alembic

El esquema se crea **únicamente** con migraciones; el proyecto no usa `create_all`.

```powershell
alembic upgrade head
```

La cabeza actual de la cadena es `0003_drop_ix_cliente_usuario_id`. Para ver el estado:

```powershell
alembic current
alembic history --verbose
```

## 5. Datos iniciales

```powershell
python scripts/seed.py
```

El script es asincrónico e idempotente: si ya hay libros, no vuelve a cargar nada. Carga 3 editoriales, 3 géneros, 4 autores, 4 libros (uno con dos autores), 2 clientes (uno con perfil) y una venta con dos renglones, suficiente para recorrer los casos C-01 a C-08.

## 6. Arrancar la API

```powershell
uvicorn app.main:app --reload
```

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Salud: <http://127.0.0.1:8000/health/live> y `/health/ready`

## 7. Endpoints

Todas las respuestas de listado son paginadas con `page` (desde 1) y `size` (1 a 100). Los errores de validación responden `422`, los recursos inexistentes `404`, los conflictos de integridad `409` y las páginas inválidas `400`.

### Salud

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health/live` | Liveness: la app está viva (no toca la base). |
| GET | `/health/ready` | Readiness: verifica la conexión a PostgreSQL. |

### Catálogo

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/editoriales/` | Alta de editorial (`201`). |
| GET | `/editoriales/` | Listado paginado. |
| GET | `/editoriales/{id}` | Detalle. |
| PATCH | `/editoriales/{id}` | Actualización parcial. |
| POST | `/generos/` | Alta de género (`201`). |
| GET | `/generos/` | Listado paginado. |
| GET | `/generos/{id}` | Detalle. |
| PATCH | `/generos/{id}` | Actualización parcial. |
| POST | `/autores/` | Alta de autor (`201`). |
| GET | `/autores/` | Listado paginado. |
| GET | `/autores/{id}` | Detalle. |
| PATCH | `/autores/{id}` | Actualización parcial. |

### Libros

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/libros/` | Alta (`201`). |
| GET | `/libros/?page=&size=&titulo=&genero_id=` | Listado con búsqueda por título (sin distinguir mayúsculas) y filtro por género. Devuelve editorial, género y autores. |
| GET | `/libros/{id}` | Detalle con editorial, género y autores. |
| PATCH | `/libros/{id}` | Actualiza ISBN, título, precio, editorial o género. **No** permite cambiar el stock. |
| PATCH | `/libros/{id}/reponer-stock` | Repone stock y registra el movimiento (`usuario_id` obligatorio). |
| DELETE | `/libros/{id}` | Baja lógica (`204`); el libro deja de aparecer en lecturas. |

Las lecturas usan carga anticipada (`joinedload` / `selectinload`) para evitar N+1: el detalle de un libro se resuelve en 2 consultas y el listado en 3, independientemente de la cantidad de autores o renglones.

### Clientes y perfil

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/clientes/` | Alta (`201`). |
| GET | `/clientes/` | Listado paginado. |
| GET | `/clientes/{id}` | Detalle. |
| PATCH | `/clientes/{id}` | Actualización parcial. |
| POST | `/clientes/{id}/perfil` | Alta del perfil (`201`). |

### Ventas

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/ventas/` | Alta transaccional (`201`); calcula el total y descuenta stock. |
| GET | `/ventas/` | Listado paginado con título de cada renglón. |
| GET | `/ventas/{id}` | Detalle con renglones. |

Las ventas no tienen `PATCH` ni `DELETE`. Un cliente o libro inexistente responde `409` y no deja filas nuevas.

## 8. Tarea en segundo plano

Al crear una venta, `POST /ventas/` encola con `BackgroundTasks` el aviso `enviar_aviso_comprobante(venta_id, total)`. La corrutina:

1. Espera `await asyncio.sleep(0.5)` sin bloquear el event loop.
2. Registra en el log: `Aviso de comprobante enviado: venta=<id> total=<total>`.

La respuesta `201` se envía antes de que el aviso termine; un fallo del aviso no revierte la venta. Mientras el aviso duerme, el servidor sigue atendiendo otras peticiones (por ejemplo `GET /health/live`). La suite lo verifica con una petición concurrente y con una auditoría estática que prohíbe `time.sleep` y `requests` en `app/`.

## 9. Pruebas automatizadas

La suite usa una base PostgreSQL real y **dedicada a tests**. No uses la base de desarrollo: los tests vacían las tablas de dominio antes de cada caso.

```powershell
$env:TEST_DATABASE_URL='postgresql+asyncpg://postgres:tu_clave@localhost:5432/libreria_test'
createdb -U postgres libreria_test
python -m pytest -q
```

En Linux / macOS:

```bash
export TEST_DATABASE_URL='postgresql+asyncpg://postgres:tu_clave@localhost:5432/libreria_test'
python -m pytest -q
```

El esquema de la base de test se crea una vez por sesión con `alembic upgrade head`, nunca con `create_all`. La suite actual tiene **69 tests** e incluye:

- contratos de paginación y validaciones;
- búsqueda de libros y actualización parcial;
- cálculo y transacción de ventas;
- perfil de cliente;
- presupuesto de consultas sin N+1 (conteo de `SELECT`);
- aviso en segundo plano y no bloqueo del event loop;
- seed idempotente;
- deriva de migraciones (`alembic check`) y coincidencia de versiones fijadas.

## 10. Estructura

```text
app/
  core/                 configuración, motor/sesiones, errores, paginación, UnitOfWork
  modules/
    health/             liveness y readiness
    editoriales/        router, service, repository, schemas, models
    generos/
    autores/
    libros/             catálogo, búsqueda, stock, soft delete, autores
    clientes/           clientes y perfil
    ventas/             venta, renglones y aviso en segundo plano
migrations/             Alembic (0001 inicial, 0002 trigger de stock, 0003 drift)
scripts/seed.py         datos iniciales idempotentes
test/                   pytest y peticiones .http
openspec/               changes archivados y specs principales
knowledge-base/         visión, modelo, reglas y decisiones del dominio
```

## 11. Reglas de implementación

- Esquema solo por Alembic; nunca `create_all`.
- Dinero con `Decimal` y `NUMERIC`, nunca `float`.
- No se pre-consulta unicidad ni existencia de ids: se escribe y la restricción responde `409`.
- Los mensajes de error no filtran tablas, restricciones ni trazas internas.
- Sin carga perezosa: `joinedload` para relaciones a uno y `selectinload` para colecciones.
- Handlers `async def`; sin llamadas bloqueantes ni SQL concatenado con datos del usuario.
- DTOs de entrada con `extra="forbid"`; nunca se devuelve `password_hash`.
- Baja de libros lógica (`borrado_en`), con índice único parcial que permite reutilizar el ISBN tras la baja.

## 12. Peticiones manuales (`.http`)

Abrí los archivos con la extensión REST Client de VS Code (o similar) y ejecutalos contra la API levantada.

> Los `.http` asumen una base recién migrada y **sin seed**: crean sus propias editoriales, géneros y autores con ids 1 y 2. Si ya ejecutaste `scripts/seed.py`, usá otra base (o ajustá ids e ISBN) para que las respuestas coincidan con los comentarios. El seed sirve para probar la API con datos representativos ya cargados.

| Caso | Archivo |
|------|---------|
| C-01 conexión y salud | `test/health.http` |
| C-02 esquema y migraciones | `alembic upgrade head` (no hay `.http`) |
| C-03 catálogo | `test/editoriales.http`, `test/generos.http`, `test/autores.http`, `test/libros.http` |
| C-04 contratos CRUD | los anteriores + `test/clientes.http` |
| C-05 ventas | `test/clientes.http`, `test/ventas.http` |
| C-06 lecturas sin N+1 | `test/libros.http`, `test/ventas.http` |
| C-07 asincronía | `test/ventas.http` (incluye la evidencia del aviso) |
| C-08 perfil y búsqueda | `test/clientes.http`, `test/libros.http` |

## 13. Problemas frecuentes

- **`Falta la variable DATABASE_URL`**: no existe `.env` o la variable no está definida en el entorno.
- **`DATABASE_URL debe usar el driver asincrónico postgresql+asyncpg`**: corregí el prefijo de la URL.
- **La suite borra datos**: `TEST_DATABASE_URL` debe apuntar a una base exclusiva de tests, nunca a `libreria`.
- **`alembic upgrade head` falla por conexión**: revisá usuario, clave, puerto y que la base exista.
- **Un `409` al crear**: el mensaje indica duplicado o referencia inválida; no se expone el detalle interno de PostgreSQL.
