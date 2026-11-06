"""Lógica de negocio del módulo generos."""

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, calcular_paginas, verificar_pagina_valida
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.core.repository import BaseRepository


async def crear_genero(session: SessionDep, data: GeneroCreate) -> GeneroRead:
    repo = BaseRepository(session, Genero)
    genero = Genero(**data.model_dump())
    await repo.add(genero)
    await session.commit()
    return GeneroRead.model_validate(genero)


async def listar_generos(
    session: SessionDep, offset: int, limit: int, page: int, size: int
) -> PaginatedResponse[GeneroRead]:
    repo = BaseRepository(session, Genero)
    total = await repo.count()
    items = await repo.get_all(offset=offset, limit=limit)
    pages = calcular_paginas(total, size)
    verificar_pagina_valida(page, pages, total)
    return PaginatedResponse[GeneroRead](
        items=[GeneroRead.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


async def obtener_genero(session: SessionDep, id: int) -> GeneroRead:
    repo = BaseRepository(session, Genero)
    genero = await repo.get_by_id(id)
    if genero is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Genero no encontrado")
    return GeneroRead.model_validate(genero)


async def actualizar_genero(
    session: SessionDep, id: int, data: GeneroUpdate
) -> GeneroRead:
    repo = BaseRepository(session, Genero)
    genero = await repo.get_by_id(id)
    if genero is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Genero no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(genero, key, value)
    await repo.update(genero)
    await session.commit()
    return GeneroRead.model_validate(genero)
