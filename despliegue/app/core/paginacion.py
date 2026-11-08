"""Paginación estándar `limit` / `offset` reutilizable por todos los listados (RN-10)."""

from typing import Annotated, NamedTuple

from fastapi import Depends, Query


class Paginacion(NamedTuple):
    limit: int
    offset: int


async def get_paginacion(
    limit: Annotated[
        int, Query(ge=1, le=100, description="Cantidad máxima de elementos (1-100)")
    ] = 20,
    offset: Annotated[int, Query(ge=0, description="Elementos a saltear (>= 0)")] = 0,
) -> Paginacion:
    """Valida `limit` y `offset`; un valor fuera de rango responde 422."""
    return Paginacion(limit=limit, offset=offset)


PaginacionDep = Annotated[Paginacion, Depends(get_paginacion)]
