"""Lógica de negocio del módulo editoriales."""

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, calcular_paginas, verificar_pagina_valida
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.core.repository import BaseRepository


async def crear_editorial(session: SessionDep, data: EditorialCreate) -> EditorialRead:
    repo = BaseRepository(session, Editorial)
    editorial = Editorial(**data.model_dump())
    await repo.add(editorial)
    await session.commit()
    return EditorialRead.model_validate(editorial)


async def listar_editoriales(
    session: SessionDep, offset: int, limit: int, page: int, size: int
) -> PaginatedResponse[EditorialRead]:
    repo = BaseRepository(session, Editorial)
    total = await repo.count()
    items = await repo.get_all(offset=offset, limit=limit)
    pages = calcular_paginas(total, size)
    verificar_pagina_valida(page, pages, total)
    return PaginatedResponse[EditorialRead](
        items=[EditorialRead.model_validate(i) for i in items],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


async def obtener_editorial(session: SessionDep, id: int) -> EditorialRead:
    repo = BaseRepository(session, Editorial)
    editorial = await repo.get_by_id(id)
    if editorial is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Editorial no encontrada")
    return EditorialRead.model_validate(editorial)


async def actualizar_editorial(
    session: SessionDep, id: int, data: EditorialUpdate
) -> EditorialRead:
    repo = BaseRepository(session, Editorial)
    editorial = await repo.get_by_id(id)
    if editorial is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Editorial no encontrada")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(editorial, key, value)
    await repo.update(editorial)
    await session.commit()
    return EditorialRead.model_validate(editorial)
