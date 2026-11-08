# Parcial — Librería (capítulos 1 a 6)

Programación III (UTN, TUP a distancia) · Comisión 4
Integrantes: Facundo Deseff, Facundo Ramírez, Santino Godoy y Matías Vargas
Repositorio: <https://github.com/FacuuRamirez1/TP_Backend>

API REST asincrónica para una librería: catálogo, clientes, ventas, stock por movimientos, autenticación con JWT en cookie HttpOnly, autorización por roles y auditoría de seguridad. Construida con **Python 3.12+, FastAPI, SQLModel, SQLAlchemy asincrónico, PostgreSQL y Alembic**, con pruebas manuales en archivos `.http`.

El esquema se crea **exclusivamente** con las migraciones de Alembic (no hay `create_all`). El archivo `.env` contiene la configuración local y no se versiona; se parte de [env.example](./env.example).

## Stack

| Capa | Tecnología |
|------|------------|
| Lenguaje | Python 3.12+ |
| Framework web | FastAPI (handlers `async def`) |
| Modelos y contratos | SQLModel |
| ORM / motor / sesión | SQLAlchemy asincrónico con asyncpg |
| Base de datos | PostgreSQL 16+ (probado con 17) |
| Migraciones | Alembic (plantilla asincrónica) |
| Configuración | pydantic-settings |
| Hash de contraseñas | bcrypt |
| Token | PyJWT en cookie HttpOnly |

## Requisitos previos

- Python 3.12 o superior.
- PostgreSQL 16 o superior (probado con PostgreSQL 17).
- Una base PostgreSQL vacía (por ejemplo `libreria`).
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

Copiá `env.example` a `.env`:

```powershell
Copy-Item env.example .env
```

Completá los datos de tu PostgreSQL y generá una clave de firma para el JWT:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

```dotenv
POSTGRES_USER=usuario
POSTGRES_PASSWORD=tu-clave
POSTGRES_DB=libreria
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
JWT_SECRET_KEY=<la-clave-generada>
```

La URL de conexión se arma sola con `POSTGRES_*` y el driver `postgresql+asyncpg`; **no** se configura `DATABASE_URL` en este proyecto.

| Variable | Obligatoria | Valor por defecto | Descripción |
|----------|-------------|-------------------|-------------|
| `POSTGRES_USER` | Sí | — | Usuario de PostgreSQL. |
| `POSTGRES_PASSWORD` | Sí | — | Contraseña de PostgreSQL (sin valor por defecto en el código). |
| `POSTGRES_DB` | Sí | — | Nombre de la base. |
| `POSTGRES_HOST` | Sí | — | Host de la base. |
| `POSTGRES_PORT` | No | `5432` | Puerto de la base. |
| `JWT_SECRET_KEY` | Sí | — | Clave de firma del JWT (sin valor por defecto). |
| `BCRYPT_COST` | No | `12` | Costo de bcrypt. |
| `DB_POOL_SIZE` | No | `5` | Tamaño del pool de conexiones. |
| `BCRYPT_CONCURRENCIA` | No | `4` | Cálculos bcrypt simultáneos (semáforo). |
| `JWT_ALGORITMO` | No | `HS256` | Algoritmo de firma del JWT. |
| `COOKIE_SECURE` | No | `false` | Flag `Secure` de la cookie de sesión. |
| `ACCESS_TOKEN_MINUTES` | No | `30` | Duración del token de acceso. |
| `SQL_ECHO` | No | `false` | Muestra las sentencias SQL en consola. |

Nunca escribas credenciales reales en el código, en `alembic.ini`, en `env.example` ni en archivos versionados. Si faltan `POSTGRES_PASSWORD` o `JWT_SECRET_KEY`, la aplicación no arranca.

## 4. Crear el esquema con Alembic

```powershell
alembic upgrade head
```

Las migraciones son cuatro:

| Revisión | Contenido |
|----------|-----------|
| `0001` | Tablas del dominio (menos `genero` y `libro.genero_id`). |
| `0002` | `genero` y `libro.genero_id` con índice y FK. |
| `0003` | Usuarios, roles, intentos, eventos, `movimiento_stock`, `cliente.usuario_id` y `libro.borrado_en`; índice único parcial de ISBN entre vigentes. |
| `0004` | Trigger que rechaza `UPDATE` y `DELETE` sobre `movimiento_stock` (solo agregado). |

Para comprobar el ciclo completo:

```powershell
alembic downgrade base
alembic upgrade head
alembic check
```

## 5. Datos iniciales

```powershell
python seed.py
```

El script es asincrónico e **idempotente**: vacía las tablas con `TRUNCATE ... RESTART IDENTITY CASCADE` y vuelve a cargar el estado inicial. Correrlo dos veces deja exactamente el mismo estado. Los hashes bcrypt se calculan antes de abrir la transacción.

Deja la base con:

- 3 editoriales (Sudamericana, Anagrama, Emecé), 3 géneros (Novela, Cuento, Ensayo) y 6 autores.
- 5 libros con su stock y un movimiento `Stock inicial` por libro.
- 3 clientes: Lucía Fernández (con perfil), Tomás Ríos (sin usuario) y Ana Paz (con el usuario `ana@example.com`).
- La venta 1, de Lucía, con 1 Rayuela y 2 Ficciones (total `69000.00`) y sus movimientos de salida.
- Una línea en `evento_seguridad` con actor `SISTEMA` y la acción `Carga de los datos iniciales`.

En los cinco libros se cumple `stock = suma(movimientos)`.

### Usuarios y contraseñas de mentira

| Correo | Contraseña | Rol | Observaciones |
|--------|------------|-----|---------------|
| `admin@example.com` | `clave-admin-1` | ADMIN | |
| `admin2@example.com` | `clave-admin-2` | ADMIN | |
| `vendedor@example.com` | `clave-vendedor-1` | VENDEDOR | |
| `ana@example.com` | `clave-ana-1` | CLIENTE | Tiene ficha de cliente. |
| `nuevo@example.com` | `clave-nuevo-1` | VENDEDOR | `debe_cambiar_password = true`. |

Las contraseñas son solo para desarrollo local y viven únicamente en `seed.py`.

## 6. Arrancar la API

```powershell
uvicorn app.main:app --reload
```

- Documentación interactiva: <http://127.0.0.1:8000/docs>
- OpenAPI: <http://127.0.0.1:8000/openapi.json>
- Salud: <http://127.0.0.1:8000/health/live> y `/health/ready`

La autenticación usa la cookie `access_token` (HttpOnly, SameSite=Lax). No se acepta el token por el cuerpo ni por la cabecera `Authorization`.

## 7. Casos de prueba `.http`

La carpeta [test/](./test/) contiene los archivos `.http` (extensión REST Client de VS Code), cada uno con su respuesta esperada en un comentario.

1. Corré `python seed.py` antes de cada archivo.
2. Abrí el `.http` en VS Code y ejecutá cada pedido desde el editor.
3. Los casos C-11, C-12 y C-13 usan varias sesiones a la vez: `# @name` guarda la respuesta y `# @no-cookie-jar` evita mezclar cookies; la cookie se pasa a mano con `Cookie: {{loginAdmin.response.headers.Set-Cookie}}`.
4. Los correos de registro llevan `{{$timestamp}}` para poder repetir la corrida.

| Caso | Qué demuestra |
|------|----------------|
| C-01 | Validación de parámetros de ruta y salud. |
| C-02 | Unicidad de ISBN y email. |
| C-03 | Un solo perfil por cliente. |
| C-04 | FK de libro inválida y alta válida. |
| C-05 | Venta con cliente o libro inexistente. |
| C-06 | Venta válida con dos renglones. |
| C-07 | Detalle de libro y venta sin N+1. |
| C-08 | Búsqueda con parámetro ligado. |
| C-09 | Paginación `{items, total, page, size, pages}`. |
| C-10 | Índice único parcial de ISBN. |
| C-11 | Registro, login, límite de intentos y cambio de contraseña. |
| C-12 | Autorización por roles, alta de personal y revocación. |
| C-13 | Stock por movimientos, baja lógica, re-alta y ventas atómicas. |
| C-14 | Seed y trigger de solo agregado (`test/solo_agregado.sql`). |

## 8. Evidencia

La carpeta [evidencia/](./evidencia/) guarda las salidas reales usadas como respaldo:

- `C-14-seed.txt`: consultas psql sobre el estado sembrado (libros, stock, venta 1, usuarios y evento `SISTEMA`).
- `C-14-solo-agregado.txt`: salida de `psql -f test/solo_agregado.sql` con el `INSERT` permitido y los `ERROR` del trigger.
- `C-15-conteo-consultas.txt`: igual número de consultas al pedir una venta con 2 y con 4 renglones.

## 9. Estructura

```text
app/
  main.py               aplicación, lifespan y registro de routers
  core/                 configuración, motor/sesiones, seguridad, errores, paginación, UoW
  modules/
    health/             liveness y readiness
    editoriales/        models, schemas, repository, unit_of_work, service, router
    generos/
    autores/
    libros/             libro, LibroAutor, MovimientoStock y el punto único de stock
    clientes/           cliente y PerfilCliente
    usuarios/           usuario, roles, intentos y eventos
    ventas/             venta, RenglonVenta y aviso en segundo plano
migrations/             Alembic (0001 a 0004)
seed.py                 datos iniciales idempotentes
test/                   casos .http y solo_agregado.sql
tests/                  pruebas automáticas con pytest
evidencia/              salidas reales de los casos
```

## 10. Pruebas automáticas

```powershell
python -m pytest -q
```

El arnés recrea una base `libreria_test`, corre `alembic upgrade head` y ejecuta las pruebas contra la app real (lifespan incluido). Necesita PostgreSQL local y leer la contraseña del entorno o de `%APPDATA%\postgresql\pgpass.conf`; nunca de un archivo versionado.

## 11. Entrega

El zip de entrega (`parcial/`) **no** debe incluir `.venv`, `__pycache__` ni `.env`. La carpeta `despliegue/` corresponde al trabajo del TP sobre un snapshot aparte.

## 12. Reglas de implementación

- Esquema solo por Alembic; nunca `create_all`.
- Dinero con `Decimal` y `NUMERIC`, nunca `float`.
- Sin carga perezosa: `joinedload` para relaciones a uno y `selectinload` para colecciones.
- Handlers `async def`; bcrypt fuera del bucle de eventos y bajo semáforo.
- Contratos de entrada con `extra="forbid"`; ninguna respuesta incluye `password_hash`.
- Los permisos se deciden con los roles vigentes en la base, no con los del token.
- `movimiento_stock` es de solo agregado y `libro.stock` se escribe en un único punto.
- Los mensajes de error no filtran tablas, restricciones ni trazas internas.
