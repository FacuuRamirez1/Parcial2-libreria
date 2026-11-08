"""Comprobación de disponibilidad de la base."""

import asyncio
import logging

from sqlalchemy import text
from sqlmodel.ext.asyncio.session import AsyncSession

LIMITE_READY_SEGUNDOS = 3

logger = logging.getLogger(__name__)


async def base_disponible(
    session: AsyncSession, limite: float = LIMITE_READY_SEGUNDOS
) -> bool:
    """True si `SELECT 1` responde dentro del límite. Registra sólo el tipo de error."""
    try:
        async with asyncio.timeout(limite):
            await session.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning("Base no disponible: %s", type(exc).__name__)
        return False
