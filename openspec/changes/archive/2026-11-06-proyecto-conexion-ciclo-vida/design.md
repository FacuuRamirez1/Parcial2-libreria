# Design

## Context

Repositorio greenfield: solo existen `knowledge-base/`, `openspec/`, `CHANGES.md`, `AGENTS.md`/`CLAUDE.md` y un `.gitignore` que ya ignora `.env` (y re-incluye `env.example`). No hay código Python, ni `requirements.txt`, ni archivos de prueba. Motivación y alcance: ver `proposal.md`. Requisitos observables: `specs/app-lifecycle/spec.md` y `specs/health/spec.md`.

Restricciones que condicionan el diseño:
- Consigna (Ejercicio 1): motor y fábrica en el `lifespan`, guardados en `app.state`, motor cerrado al apagar; sesión con `Depends(get_session)`, una por petición, `expire_on_commit=False`; `DATABASE_URL` desde `.env`.
- Stack fijado por la KB: Python 3.12, FastAPI ≥ 0.111, SQLModel ≥ 0.0.24, SQLAlchemy 2 async, asyncpg ≥ 0.30, python-dotenv ≥ 1.0. PostgreSQL 16 local por integrante, sin Docker (DD-03).
- Reglas duras (`AGENTS.md`): nunca `create_all`, nunca llamadas bloqueantes en handlers, nunca credenciales en el repo, sin repositorios/UoW.
- La consigna exige que las pruebas sean sólo archivos `.http` en `test/`; no hay tests automatizados (ver D-06).

## Goals / Non-Goals

**Goals:**
- Dejar `SessionDep` y la estructura de módulos como contrato estable para C-02..C-07.
- Que el arranque no dependa de que PostgreSQL esté encendido (el motor conecta en forma perezosa); sólo `/health/ready` toca la base.
- Que cada comportamiento tenga una verificación concreta y reproducible: una petición en `test/health.http` con la respuesta esperada comentada, o una comprobación manual (consola de uvicorn, arranque sin `.env`).

**Non-Goals:**
- Pool tuning, `pool_pre_ping`, middlewares (CORS, request-id, timing), logging estructurado.
- `pydantic-settings` (el stack de la consigna fija `python-dotenv`).
- Handler global de `IntegrityError` (C-04), Alembic y `scripts/seed.py` (C-03).
- Tests automatizados (ver D-06).

## Decisions

### D-01 — Configuración: `python-dotenv` + función de validación sin efectos
`app/core/config.py` expone:
- `Configuracion` (dataclass congelada): `database_url: str`, `sql_echo: bool`.
- `leer_configuracion(entorno: Mapping[str, str]) -> Configuracion`: función **pura** (sin leer el entorno por su cuenta; se mantiene separada de `get_settings` sólo para dejar la validación en un único lugar legible, no por testabilidad); valida que `DATABASE_URL` exista, no esté vacía y empiece con `postgresql+asyncpg://`; interpreta `SQL_ECHO` (`true/1/yes/on`, sin distinguir mayúsculas → `True`; cualquier otro valor o ausencia → `False`). Lanza `ErrorDeConfiguracion` (subclase de `RuntimeError`) con mensaje que nombra la variable pero **nunca incluye su valor**.
- `get_settings() -> Configuracion`: llama `load_dotenv(RAIZ / ".env", override=False)` (el entorno del proceso prevalece) y luego `leer_configuracion(os.environ)`.

Ruta explícita del `.env` (raíz del proyecto calculada desde `config.py`) en lugar de `find_dotenv()`, para que el resultado no dependa del directorio de trabajo desde el que se lanza uvicorn.

`get_settings()` se llama **dentro del `lifespan`**, no al importar: importar `app.main` no exige `.env` (se puede importar el paquete sin configuración) y una configuración inválida hace fallar el arranque con "Application startup failed" y el mensaje propio.

*Alternativas*: `pydantic-settings` (más validación, pero agrega una dependencia fuera del stack de la consigna); leer config a nivel de módulo (rompe importación en tests sin `.env`).

### D-02 — Motor y fábrica en el `lifespan`, guardados en `app.state`
`app/core/database.py`:
- `crear_motor(cfg) -> AsyncEngine`: `create_async_engine(cfg.database_url, echo=cfg.sql_echo)`. Sin `pool_pre_ping` (ver riesgos).
- `crear_fabrica_sesiones(engine) -> async_sessionmaker[AsyncSession]`: `async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)`, con `AsyncSession` de `sqlmodel.ext.asyncio.session` (para que C-04+ usen `session.exec(select(...))` como indica la skill `sqlmodel`).

`app/main.py`: `lifespan` con `@asynccontextmanager` (no `on_event`, deprecado): `cfg = get_settings()`, `app.state.engine = crear_motor(cfg)`, `app.state.session_factory = crear_fabrica_sesiones(engine)`; `yield`; en `finally`, `await app.state.engine.dispose()`.

*Alternativas*: motor global a nivel de módulo (lo que la consigna pide evitar; no cierra conexiones al apagar).

### D-03 — `get_session` y alias `SessionDep`
```python
async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.session_factory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]
```
El `async with` garantiza el cierre aun si el handler lanza. `get_session` **no** hace commit automático: cada service confirma explícitamente (C-04+ decide sus transacciones). Se toma la fábrica desde `request.app.state` (no de un global), como pide la consigna. Estilo `Annotated` según skill `fastapi`.

### D-04 — Health: router + service, contrato de respuesta (resuelve pregunta abierta "estado de la base")
- `app/modules/health/schemas.py`: `EstadoVida(estado: str)` y `EstadoDisponibilidad(estado: str, base: str)` (SQLModel sin `table=True`).
- `app/modules/health/service.py`: `async def base_disponible(session, limite: float = LIMITE_READY_SEGUNDOS) -> bool` — dentro de `asyncio.timeout(limite)` ejecuta `await session.execute(text("SELECT 1"))`; devuelve `True`; ante `Exception` o `TimeoutError` registra en el log sólo el **tipo** de excepción (`type(exc).__name__`, nunca la URL ni el mensaje del driver) y devuelve `False`. No captura `BaseException` (la cancelación se propaga). `LIMITE_READY_SEGUNDOS = 3` (spec exige ≤ 5 s).
- `app/modules/health/router.py`: `APIRouter(prefix="/health", tags=["health"])`.
  - `GET /live -> EstadoVida`: no recibe sesión; devuelve `{"estado": "vivo"}`.
  - `GET /ready -> EstadoDisponibilidad`: recibe `SessionDep` y `Response`; si `base_disponible` → 200 `{"estado": "listo", "base": "conectada"}`; si no → `response.status_code = 503` y `{"estado": "no listo", "base": "sin conexión"}`.

Se usa `session.execute(text(...))` (no `exec`) porque es SQL textual sin modelo; es SQL fijo, sin datos del usuario (NF-03 no aplica). 503 es el código estándar para "dependencia no disponible"; la consigna sólo define el caso exitoso.

*Alternativas*: lanzar `HTTPException(503, detail=...)` (cambia la forma del cuerpo a `{"detail": ...}`, inconsistente con el éxito); usar `engine.connect()` directo (no ejercitaría `get_session`, que es lo que la consigna evalúa).

### D-05 — Esqueleto de módulos y registro de routers
Los 7 módulos con `__init__.py`, `models.py`, `schemas.py`, `service.py`, `router.py`. En los 6 módulos de dominio:
- `models.py`, `schemas.py`, `service.py`: sólo docstring indicando el change que los completa (C-02 / C-04 / C-05).
- `router.py`: `router = APIRouter(prefix="/<modulo>", tags=["<modulo>"])` sin rutas.

`main.py` **registra sólo `health.router`**. Cada change que agregue rutas a un módulo agrega su `include_router` (C-04/C-05). Así `/docs` no muestra grupos vacíos y el registro queda ligado a contenido real. Paquetes `app/`, `app/core/`, `app/modules/` con `__init__.py`.

### D-06 — Verificación: sólo archivos `.http` y comprobaciones manuales
La consigna exige que las pruebas sean archivos `.http` dentro de `test/`; por eso **no se usan tests automatizados**: ni `pytest`, ni `pytest-asyncio`, ni `httpx`, ni `requirements-dev.txt`, ni configuración de pytest. Los tests automáticos quedan fuera de alcance.
- `test/health.http`: `GET {{base}}/health/live` y `GET {{base}}/health/ready`, cada uno con la respuesta esperada comentada (200 vivo; 200 listo/conectada; 503 no listo/sin conexión con la base apagada).
- Comprobaciones manuales (sin `.http`): arranque sin `.env` o con `DATABASE_URL` inválida falla con mensaje claro y sin valor de la variable; `SQL_ECHO=true` muestra `SELECT 1` en la consola de uvicorn; `Ctrl+C` apaga sin advertencias de conexiones sin cerrar (`engine.dispose()`); import de los 7 módulos con `python -c`; `grep` de reglas duras.
- `pyproject.toml` se reduce a `[tool.fastapi] entrypoint = "app.main:app"` (skill `fastapi`), para `fastapi dev`.
- Respuesta lenta de la base: se comprueba apuntando `DATABASE_URL` a un host no ruteable (p. ej. `10.255.255.1`) y verificando en el `.http` que `/health/ready` responde 503 en ≈ 3 s.

### D-07 — Dependencias fijadas
`requirements.txt` (runtime): `fastapi[standard]`, `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg`, `python-dotenv`, todas con `==`. Versión exacta: la última estable instalada en el apply que cumpla los mínimos de la KB (FastAPI ≥ 0.111, SQLModel ≥ 0.0.24, SQLAlchemy ≥ 2.0, asyncpg ≥ 0.30, python-dotenv ≥ 1.0), tomada de `pip freeze` sólo para los paquetes de primer nivel. `alembic` **no** se agrega acá: lo agrega C-03.

### D-08 — Ubicación del script de datos iniciales (resuelve pregunta abierta)
`scripts/seed.py` en la raíz del repo (fuera de `app/`), async, reutilizando `get_settings`, `crear_motor` y `crear_fabrica_sesiones`. **Se implementa en C-03**, no en C-01; C-01 no crea la carpeta `scripts/`.

### D-09 — README mínimo
`README.md` con: crear venv (Python 3.12), `pip install -r requirements.txt`, copiar `env.example` a `.env`, crear la base `libreria` en PostgreSQL 16 local, `uvicorn app.main:app --reload` (o `fastapi dev`), cómo ejecutar `test/health.http`. Sección "pendiente" para `alembic upgrade head` y seed. C-07 lo reescribe completo.

## Risks / Trade-offs

- [Sin `pool_pre_ping`, una conexión del pool cortada por el servidor falla en el primer uso] → aceptable en desarrollo local; evita sentencias extra en la consola que ensuciarían la evidencia de C-06/C-07. Se puede agregar luego sin cambiar specs.
- [Capturar `Exception` en `/health/ready` podría ocultar un bug de programación] → se loguea el tipo de excepción; el alcance del `try` es sólo la ejecución de `SELECT 1`.
- [`asyncio.timeout` cancela la operación a mitad de conexión] → la sesión se cierra igual por el `async with` de `get_session`; el motor descarta la conexión inválida.
- [Diferencias de entorno entre integrantes (puerto, usuario, versión), DD-03] → `env.example` documenta la forma; `/health/ready` devuelve 503 en lugar de fallar si no hay base.
- [Fijar versiones "la última al momento del apply" puede variar entre integrantes si instalan antes de que se versione `requirements.txt`] → una sola persona genera `requirements.txt` en el apply; el resto instala desde el archivo.
- [Windows: asyncpg con el event loop por defecto] → asyncpg soporta el Proactor loop de Windows; si aparece un problema se documenta en el README.

## Migration Plan

No aplica (proyecto nuevo, sin datos ni despliegue). Rollback: revertir el commit del change.

## Open Questions

- Ninguna que bloquee. Las dos preguntas abiertas de `10_preguntas_abiertas.md` que tocaban a C-01 quedan resueltas en D-04 (cuerpo de `/health/ready`) y D-08 (ubicación del seed); conviene reflejarlo en la KB al archivar.
