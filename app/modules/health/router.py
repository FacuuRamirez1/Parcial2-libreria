"""Sondas de vida y de disponibilidad de la base."""

from fastapi import APIRouter, HTTPException, status

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
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Base no disponible",
    )
