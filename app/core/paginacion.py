"""Paginación estándar reutilizable por todos los listados de la API."""

from math import ceil
from typing import Generic, TypeVar

from fastapi import HTTPException, Query
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


def calcular_paginas(total: int, size: int) -> int:
    """Devuelve 1 si total == 0, otherwise ceil(total / size)."""
    if total == 0:
        return 1
    return ceil(total / size)


class PaginatedResponse(BaseModel, Generic[T]):
    """Respuesta paginada genérica con exactamente los campos requeridos."""

    model_config = ConfigDict(from_attributes=True)

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def paginar(items: list[T], total: int, page: int, size: int) -> PaginatedResponse[T]:
    """Construye la respuesta paginada.

    Si total == 0 -> pages = 1, items = [].
    Si total > 0 y page > pages -> HTTPException 422.
    """
    pages = calcular_paginas(total, size)
    if total > 0 and page > pages:
        raise HTTPException(status_code=422, detail="Página fuera de rango")
    if total == 0:
        return PaginatedResponse(items=[], total=0, page=page, size=size, pages=1)
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


def verificar_pagina_valida(page: int, pages: int, total: int) -> None:
    """Lanza HTTPException 422 cuando la página solicitada está fuera de rango."""
    if total > 0 and page > pages:
        raise HTTPException(status_code=422, detail="Página fuera de rango")


async def get_paginacion(
    page: int = Query(1, ge=1, description="Número de página (>= 1)"),
    size: int = Query(20, ge=1, le=100, description="Tamaño de página (1-100)"),
) -> tuple[int, int]:
    """Valida page/size y devuelve la tupla (page, size)."""
    return page, size
