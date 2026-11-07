"""Punto de entrada de la API: ciclo de vida del motor y registro de routers."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.errors import init_error_handlers
from app.core.database import crear_fabrica_sesiones, crear_motor
import app.models  # noqa: F401  (registra todos los mappers antes de la primera consulta)
from app.modules.autores.router import router as autores_router
from app.modules.clientes.router import router as clientes_router
from app.modules.editoriales.router import router as editoriales_router
from app.modules.generos.router import router as generos_router
from app.modules.health.router import router as health_router
from app.modules.libros.router import router as libros_router
from app.modules.ventas.router import router as ventas_router


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    cfg = get_settings()
    engine = crear_motor(cfg)
    app.state.engine = engine
    app.state.session_factory = crear_fabrica_sesiones(engine)
    try:
        yield
    finally:
        await engine.dispose()


configurar_logging()
app = FastAPI(lifespan=lifespan)
init_error_handlers(app)

app.include_router(health_router)
app.include_router(editoriales_router)
app.include_router(generos_router)
app.include_router(autores_router)
app.include_router(libros_router)
app.include_router(clientes_router)
app.include_router(ventas_router)
