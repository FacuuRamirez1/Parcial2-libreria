"""Punto de entrada de la API: ciclo de vida del motor y registro de routers."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.core.database import crear_fabrica_sesiones, crear_motor
from app.modules.health.router import router as health_router


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


app = FastAPI(lifespan=lifespan)
app.include_router(health_router)
