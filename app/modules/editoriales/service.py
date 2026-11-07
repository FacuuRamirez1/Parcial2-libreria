"""Lógica de negocio del módulo editoriales (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.repositorios.
"""

from fastapi import HTTPException
from sqlmodel import select

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.editoriales.unit_of_work import EditorialesUnitOfWork
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead

MENSAJE_NO_ENCONTRADA = "Editorial no encontrada"


async def _obtener(uow: EditorialesUnitOfWork, id: int) -> Editorial:
    editorial = await uow.editoriales.get_by_id(id)
    if editorial is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADA)
    return editorial


async def crear_editorial(uow: EditorialesUnitOfWork, data: EditorialCreate) -> EditorialRead:
    async with uow:
        editorial = Editorial(**data.model_dump())
        await uow.editoriales.add(editorial)
        return EditorialRead.model_validate(editorial)


async def listar_editoriales(uow: EditorialesUnitOfWork, pag: Paginacion) -> PaginatedResponse[EditorialRead]:
    async with uow:
        total = await uow.editoriales.count()
        verificar_pagina(pag.page, total, pag.size)
        items = await uow.editoriales.get_all(offset=pag.offset, limit=pag.limit)
        return PaginatedResponse(
            items=[EditorialRead.model_validate(e) for e in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )


async def obtener_editorial(uow: EditorialesUnitOfWork, id: int) -> EditorialRead:
    async with uow:
        return EditorialRead.model_validate(await _obtener(uow, id))


async def actualizar_editorial(
    uow: EditorialesUnitOfWork, id: int, data: EditorialUpdate
) -> EditorialRead:
    async with uow:
        editorial = await _obtener(uow, id)
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(editorial, campo, valor)
        await uow.editoriales.update(editorial)
        return EditorialRead.model_validate(editorial)


async def listar_libros_de_editorial(
    uow: EditorialesUnitOfWork, id: int, pag: Paginacion
) -> PaginatedResponse[LibroRead]:
    async with uow:
        await _obtener(uow, id)
        from sqlalchemy import func

        total = await uow.session.exec(
            select(func.count()).select_from(Libro).where(Libro.editorial_id == id)
        )
        total = total.one()
        verificar_pagina(pag.page, total, pag.size)
        resultado = await uow.session.exec(
            select(Libro)
            .where(Libro.editorial_id == id)
            .order_by(Libro.id)
            .offset(pag.offset)
            .limit(pag.limit)
        )
        items = resultado.all()
        return PaginatedResponse(
            items=[LibroRead.model_validate(l) for l in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )
