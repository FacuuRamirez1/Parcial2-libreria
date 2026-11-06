"""Sondas de vida y de disponibilidad de la base."""

from fastapi import APIRouter

from app.core.database import SessionDep
from app.modules.health.schemas import EstadoDisponibilidad, EstadoVida
from app.modules.health.service import base_disponible

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def live() -> EstadoVida:
    return EstadoVida(estado="vivo")


@router.get("/ready")
async def ready(session: SessionDep) -> EstadoDisponibilidad:
    if await base_disponible(session):
        return EstadoDisponibilidad(estado="listo", base="conectada")
    return EstadoDisponibilidad(estado="no listo", base="sin conexión")
