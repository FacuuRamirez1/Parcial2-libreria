# Tasks

> Verificación sólo con archivos `.http` en `test/` (como exige la consigna) y comprobaciones manuales; no hay tests automatizados (`design.md` D-06). Cada tarea indica cómo se verifica. Referencias: `design.md` (D-01..D-09), `specs/app-lifecycle/spec.md`, `specs/health/spec.md`.
> Recordatorio de reglas duras: sin `create_all`, sin credenciales en el repo, todo handler `async def`, no recrear `.gitignore`, no commitear sin orden del usuario.

## 1. Entorno y dependencias

- [x] 1.1 Crear venv con Python 3.12, instalar `fastapi[standard]`, `sqlmodel`, `sqlalchemy[asyncio]`, `asyncpg`, `python-dotenv` y escribir `requirements.txt` con versiones exactas (`==`) de esos paquetes de primer nivel tomadas de `pip freeze` (D-07). Verificación manual: `pip install -r requirements.txt` en un venv limpio termina sin errores y las versiones cumplen los mínimos de la KB
- [x] 1.2 Crear `pyproject.toml` con `[tool.fastapi] entrypoint = "app.main:app"` (D-06). Verificación manual: `fastapi dev` (o `uvicorn app.main:app`) encuentra la app
- [x] 1.3 Crear `env.example` con `DATABASE_URL=postgresql+asyncpg://usuario:clave@localhost:5432/libreria` y `SQL_ECHO=false`, comentados. Verificación manual: `git check-ignore -v .env` confirma que `.env` está ignorado y `git check-ignore env.example` (sin salida) que no lo está. No modificar `.gitignore`

## 2. Estructura de módulos

- [x] 2.1 Crear `app/__init__.py`, `app/core/__init__.py`, `app/modules/__init__.py` y los 7 paquetes de módulo con `__init__.py`, `models.py`, `schemas.py`, `service.py`, `router.py`; en los 6 de dominio, docstring con el change que los completa y `router = APIRouter(prefix="/<modulo>", tags=["<modulo>"])` sin rutas (D-05). Verificación manual: `python -c "import importlib; [importlib.import_module(f'app.modules.{m}.{p}') for m in ('health','editoriales','generos','autores','libros','clientes','ventas') for p in ('models','schemas','service','router')]"` termina sin error; `grep -rn "create_all" app/` sin resultados

## 3. Configuración por entorno

- [x] 3.1 Implementar en `app/core/config.py` `Configuracion`, `ErrorDeConfiguracion`, `leer_configuracion(Mapping)` (función pura, D-01) y `get_settings()` con `load_dotenv(RAIZ / ".env", override=False)`. Verificación manual (arranque): sin `.env` ni `DATABASE_URL`, `uvicorn app.main:app` falla con "Application startup failed" y un mensaje que nombra `DATABASE_URL`; con `DATABASE_URL=postgresql://usuario:clave@...` el mensaje menciona `postgresql+asyncpg` y **no** muestra `clave`; con una variable de entorno `DATABASE_URL` distinta a la del `.env`, prevalece la del entorno
- [x] 3.2 Verificar `SQL_ECHO` (manual, junto con 6.3): `true`/`TRUE`/`1`/`yes`/`on` activan el eco de SQL en la consola; ausente, `false` o un valor no reconocido (`quizas`) no lo activan

## 4. Motor, fábrica de sesiones y lifespan

- [x] 4.1 Implementar `crear_motor` (con `echo=cfg.sql_echo`) y `crear_fabrica_sesiones` (`async_sessionmaker` con `sqlmodel.ext.asyncio.session.AsyncSession` y `expire_on_commit=False`) en `app/core/database.py` (D-02). Verificación manual: se revisa el código contra la spec y se comprueba en 6.3 que las consultas se ejecutan
- [x] 4.2 Implementar `lifespan` con `@asynccontextmanager` en `app/main.py` (`get_settings()` → motor y fábrica en `app.state`; `dispose()` en `finally`), crear `app = FastAPI(lifespan=lifespan)` e incluir sólo `health.router` (D-02, D-05). Verificación manual: con la base APAGADA, `uvicorn app.main:app` arranca igual y `GET /health/live` en `test/health.http` responde 200 `{"estado": "vivo"}`; con `Ctrl+C` el proceso termina sin advertencias de conexiones sin cerrar (motor liberado con `dispose()`)

## 5. Sesión por petición

- [x] 5.1 Implementar `get_session` (con `async with`, sin commit automático) y `SessionDep = Annotated[AsyncSession, Depends(get_session)]` en `app/core/database.py` (D-03). Verificación manual: `GET /health/ready` repetido en `test/health.http` con SQL_ECHO activo muestra un `SELECT 1` por petición y no acumula conexiones abiertas (el servidor no reporta conexiones colgadas en `pg_stat_activity` tras las peticiones)

## 6. Health

- [x] 6.1 Implementar `app/modules/health/schemas.py` (`EstadoVida`, `EstadoDisponibilidad`), `service.py` (`base_disponible` con `asyncio.timeout`, log sólo del tipo de excepción, `LIMITE_READY_SEGUNDOS = 3`) y `router.py` (`/health/live`, `/health/ready` con `SessionDep` y `Response` para el 503) (D-04)
- [x] 6.2 Crear `test/health.http` con `GET {{base}}/health/live` y `GET {{base}}/health/ready` y las respuestas esperadas comentadas: `/live` → 200 `{"estado": "vivo"}`; `/ready` con base encendida → 200 `{"estado": "listo", "base": "conectada"}`; `/ready` con la base apagada → 503 `{"estado": "no listo", "base": "sin conexión"}`. Verificación (`.http` contra `uvicorn app.main:app`): ejecutar las dos peticiones con la base encendida y luego apagada; en el 503 el cuerpo no contiene host, usuario ni mensaje del driver, y `/live` sigue en 200
- [x] 6.3 Verificación manual de `SQL_ECHO` y demora: con `SQL_ECHO=true` y base encendida, `/health/ready` imprime `SELECT 1` en la consola de uvicorn; con `SQL_ECHO=false` no se imprime. Con `DATABASE_URL` apuntando a un host no ruteable (p. ej. `10.255.255.1`), `/health/ready` responde 503 en unos 3 s (≤ 5 s) y `/health/live` sigue en 200

## 7. Documentación e integración final

- [x] 7.1 Escribir `README.md` mínimo (D-09): venv Python 3.12, `pip install -r requirements.txt`, copiar `env.example` a `.env`, crear base `libreria` en PostgreSQL 16 local, arrancar con `uvicorn app.main:app --reload`, ejecutar `test/health.http`; sección "pendiente" para `alembic upgrade head` (C-03) y seed (`scripts/seed.py`, C-03). Verificación manual: seguir los pasos desde un venv limpio
- [x] 7.2 Verificación integral (manual + `.http`): flujo completo de 6.2 y 6.3; tras `Ctrl+C` el proceso termina limpio; la base sigue sin tablas (`\dt` en `psql` vacío)
- [x] 7.3 Auditoría de reglas duras (manual): `grep -rn "create_all\|time.sleep\|import requests" app/` sin resultados; ningún `def` de handler sin `async`; `git status` no muestra `.env`; ningún archivo versionable contiene credenciales reales

## Workflow follow-up

- Marcar en `knowledge-base/10_preguntas_abiertas.md` como resueltas las preguntas de `/health/ready` (D-04) y ubicación del seed (D-08).
- Archivar con `/opsx:archive proyecto-conexion-ciclo-vida` y marcar `[x]` C-01 en `CHANGES.md`.
