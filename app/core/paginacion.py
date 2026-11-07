"""Paginación estándar por página/tamaño reutilizable por todos los listados.

Contrato de consulta: page (>= 1, def. 1) y size (1-100, def. 20). La clase
Paginacion conserva las propiedades limit/offset de compatibilidad para que los
servicios de dominio (C-09 las migrará a capas) no necesiten cambios en C-08.
"""

import math
from typing import Annotated, Generic, TypeVar

from fastapi import Depends, HTTPException, Query
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Envoltorio genérico {items, total, page, size, pages}."""

    items: list[T]
    total: int
    page: int
    size: int
    pages: int


def calcular_paginas(total: int, size: int) -> int:
    """Devuelve 1 si total == 0, si no ceil(total / size)."""
    if total == 0:
        return 1
    return math.ceil(total / size)


def verificar_pagina(page: int, size: int, total: int) -> None:
    """Lanza HTTPException 422 si la página solicitada excede el total (total > 0)."""
    if total > 0 and page > calcular_paginas(total, size):
        raise HTTPException(status_code=422, detail="Página fuera de rango")


class Paginacion:
    """Contrato page/size con propiedades limit/offset de compatibilidad."""

    def __init__(self, page: int = 1, size: int = 20) -> None:
        self.page = page
        self.size = size

    @property
    def limit(self) -> int:
        return self.size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


async def get_paginacion(
    page: Annotated[int, Query(ge=1, description="Página (>= 1)")] = 1,
    size: Annotated[
        int, Query(ge=1, le=100, description="Elementos por página (1-100)")
    ] = 20,
) -> Paginacion:
    """Valida page y size; un valor fuera de rango responde 422."""
    return Paginacion(page=page, size=size)


PaginacionDep = Annotated[Paginacion, Depends(get_paginacion)]
