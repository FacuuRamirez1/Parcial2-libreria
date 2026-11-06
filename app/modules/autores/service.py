"""Lógica de negocio del módulo autores."""

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, calcular_paginas, verificar_pagina_valida
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.core.repository import BaseRepository


async def crear_autor(session: SessionDep, data: AutorCreate) -> AutorRead:
    repo = BaseRepository(session, Autor)
    autor = Autor(**data.model_dump())
    await repo.add(autor)
    await session.commit()
    return AutorRead.model_validate(autor)


async def listar_autores(
    session: SessionDep, offset: int, limit: int, page: int, size: int
) -> PaginatedResponse[AutorRead]:
    repo = BaseRepository(session, Autor)
    total = await repo.count()
    items = await repo.get_all(offset=offset, limit=limit)
    pages = calcular_paginas(total, size)
    verificar_pagina_valida(page, pages, total)
    return PaginatedResponse[AutorRead](
        items=[AutorRead.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


async def obtener_autor(session: SessionDep, id: int) -> AutorRead:
    repo = BaseRepository(session, Autor)
    autor = await repo.get_by_id(id)
    if autor is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Autor no encontrado")
    return AutorRead.model_validate(autor)


async def actualizar_autor(
    session: SessionDep, id: int, data: AutorUpdate
) -> AutorRead:
    repo = BaseRepository(session, Autor)
    autor = await repo.get_by_id(id)
    if autor is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Autor no encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(autor, key, value)
    await repo.update(autor)
    await session.commit()
    return AutorRead.model_validate(autor)
