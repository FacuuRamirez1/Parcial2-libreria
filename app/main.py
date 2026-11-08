"""Punto de entrada de la API: ciclo de vida del motor y registro de routers."""

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI

from app.core.config import Settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.core.dependencies import exigir_password_al_dia
from app.core.errors import init_error_handlers
from app.core.security import calcular_hash_ficticio
import app.models  # noqa: F401  (registra todos los mappers antes de la primera consulta)
from app.modules.autores import router as autores
from app.modules.clientes import router as clientes
from app.modules.editoriales import router as editoriales
from app.modules.generos import router as generos
from app.modules.health.router import router as health_router
from app.modules.libros import router as libros
from app.modules.usuarios.router import eventos_router, personal_router
from app.modules.usuarios.router import router as auth_router
from app.modules.ventas import router as ventas


def configurar_logging() -> None:
    """Hace visible en la consola el log INFO de la app (p. ej. el aviso del comprobante).

    Uvicorn solo configura sus propios loggers: sin esto, los `logger.info` de `app.*`
    se descartan porque el logger raíz trabaja en WARNING. Los propaga igual al raíz,
    de modo que `caplog` los sigue capturando en las pruebas.
    """
    logger = logging.getLogger("app")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        manejador = logging.StreamHandler()
        manejador.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
        logger.addHandler(manejador)


configurar_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = Settings()  # falla con mensaje claro si faltan JWT_SECRET_KEY / POSTGRES_PASSWORD
    app.state.settings = settings
    # El semáforo se crea aquí, ya dentro del bucle de eventos (nunca al importar el módulo).
    app.state.semaforo_bcrypt = asyncio.Semaphore(settings.BCRYPT_CONCURRENCIA)
    engine = crear_motor(settings)
    app.state.engine = engine
    app.state.session_factory = crear_fabrica_sesiones(engine)
    # Hash ficticio calculado una vez al arrancar (fuera del bucle de eventos).
    app.state.hash_ficticio = await calcular_hash_ficticio(settings.BCRYPT_COST)
    try:
        yield
    finally:
        await engine.dispose()


configurar_logging()
app = FastAPI(lifespan=lifespan)
init_error_handlers(app)

# Dos grupos de rutas, no uno: FastAPI SUMA las dependencias (app + router padre + router hijo +
# ruta) y no tiene forma de RESTARLAS. Si `exigir_password_al_dia` (RN-06) colgara de la app o de
# un router común, `/auth/cambiar-password` (la única salida del bloqueo) también quedaría
# bloqueada. Por eso el control se monta UNA sola vez, sobre el grupo protegido; el abierto lleva
# health, /auth y las lecturas públicas del catálogo. El rol de cada ruta (`requiere_rol`) se
# declara en el router de su módulo, no aquí (no todas las rutas protegidas piden el mismo rol).
abierto = APIRouter()
protegido = APIRouter(dependencies=[Depends(exigir_password_al_dia)])

abierto.include_router(health_router)
abierto.include_router(auth_router)
for modulo in (editoriales, generos, autores, libros):
    abierto.include_router(modulo.router_abierto)
    protegido.include_router(modulo.router_protegido)
protegido.include_router(clientes.router_protegido)
protegido.include_router(ventas.router_protegido)
protegido.include_router(ventas.router_mis_ventas)
protegido.include_router(personal_router)
protegido.include_router(eventos_router)

app.include_router(abierto)
app.include_router(protegido)
