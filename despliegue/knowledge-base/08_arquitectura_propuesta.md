# Arquitectura Propuesta

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| Organización por módulo funcional | `app/modules/<módulo>/` | Misma estructura en los 7 módulos; lo exige la consigna |
| Separación tabla / contrato | `models.py` vs `schemas.py` | Los DTO de alta no llevan `id`; evita exponer o aceptar campos internos |
| Service con sesión por parámetro | `service.py` | La lógica no depende de FastAPI; sin repositorios ni UoW (capítulo 6 fuera) |
| Inyección de dependencias | `Depends(get_session)` | Una sesión por petición, `expire_on_commit=False` |
| Recursos en lifespan | `main.py` | Motor y fábrica de sesiones en `app.state`; el motor se cierra al apagar |
| Objeto de asociación | `LibroAutor` | Guarda `rol` y `orden`, que no son ni del libro ni del autor |
| Carga anticipada | consultas de lectura | `joinedload` (a uno) y `selectinload` (colecciones); sin N+1 |
| Garantías en la base | UNIQUE, CHECK, FK | La unicidad no se verifica con consulta previa; `IntegrityError` → 409 |
| Tarea en segundo plano | alta de venta | `BackgroundTasks` con aviso simulado |

## Estructura de directorios

```
Parcial2-libreria/
├── app/
│   ├── main.py                  # app, lifespan, registro de routers
│   ├── core/
│   │   ├── config.py            # lee DATABASE_URL del entorno
│   │   └── database.py          # motor, fábrica de sesiones, get_session
│   └── modules/
│       ├── health/
│       ├── editoriales/
│       ├── generos/
│       ├── autores/
│       ├── libros/              # incluye LibroAutor
│       ├── clientes/            # incluye PerfilCliente
│       └── ventas/              # incluye RenglonVenta
│           ├── models.py
│           ├── schemas.py
│           ├── service.py
│           └── router.py
├── migrations/                  # Alembic (plantilla async) y versions/
├── test/                        # archivos .http (casos C-01 a C-08)
├── alembic.ini                  # sin credenciales
├── env.example
├── requirements.txt
├── README.md
└── knowledge-base/ · openspec/ · discovery/
```

El script de datos iniciales se ubica fuera de `app/` (propuesta: `scripts/seed.py`); la ubicación exacta es una decisión del change correspondiente.

## Seguridad

- **Autenticación / autorización:** fuera de alcance (capítulo 5).
- **Validación de input:** DTO de Pydantic/SQLModel y restricciones en `Query` y `Path`; el error de tipos responde 422.
- **Inyección SQL:** parámetros ligados siempre; nunca SQL concatenado (C-08).
- **Errores:** mensajes propios; nunca nombres de tablas, restricciones ni trazas de la base.
- **Secrets:** `DATABASE_URL` solo en `.env` (no versionado) y `env.example` sin valores reales; nada en `alembic.ini`.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | URL de conexión asincrónica a PostgreSQL | `postgresql+asyncpg://usuario:clave@localhost:5432/libreria` | Sí |
| `SQL_ECHO` (propuesta) | Muestra las consultas en consola (requisito de diagnóstico, C-07) | `true` | No |

> `SQL_ECHO` no figura en la consigna, que solo pide que el `echo` sea configurable. El nombre es una decisión nuestra.

## Entorno de desarrollo

Cada integrante instala PostgreSQL 16 en forma local y define su propio `.env` a partir de `env.example`. No hay Docker/Compose. Pasos del README: entorno virtual, dependencias, `.env`, `alembic upgrade head`, datos iniciales y arranque con uvicorn.
