"""Lógica de negocio del módulo autores (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.repositorios.
"""

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.autores.unit_of_work import AutoresUnitOfWork
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import LibroDeAutorRead, LibroRead

MENSAJE_NO_ENCONTRADO = "Autor no encontrado"


async def _obtener(uow: AutoresUnitOfWork, id: int) -> Autor:
    autor = await uow.autores.get_by_id(id)
    if autor is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return autor


async def crear_autor(uow: AutoresUnitOfWork, data: AutorCreate) -> AutorRead:
    async with uow:
        autor = Autor(**data.model_dump())
        await uow.autores.add(autor)
        return AutorRead.model_validate(autor)


async def listar_autores(uow: AutoresUnitOfWork, pag: Paginacion) -> PaginatedResponse[AutorRead]:
    async with uow:
        total = await uow.autores.count()
        verificar_pagina(pag.page, total, pag.size)
        items = await uow.autores.get_all(offset=pag.offset, limit=pag.limit)
        return PaginatedResponse(
            items=[AutorRead.model_validate(a) for a in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )


async def obtener_autor(uow: AutoresUnitOfWork, id: int) -> AutorRead:
    async with uow:
        return AutorRead.model_validate(await _obtener(uow, id))


async def actualizar_autor(
    uow: AutoresUnitOfWork, id: int, data: AutorUpdate
) -> AutorRead:
    async with uow:
        autor = await _obtener(uow, id)
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(autor, campo, valor)
        await uow.autores.update(autor)
        return AutorRead.model_validate(autor)


async def listar_libros_de_autor(
    uow: AutoresUnitOfWork, id: int, pag: Paginacion
) -> PaginatedResponse[LibroDeAutorRead]:
    """Libros del autor con rol y orden de cada autoría (una consulta fija)."""
    async with uow:
        await _obtener(uow, id)
        from sqlalchemy import func

        total = await uow.session.exec(
            select(func.count()).select_from(LibroAutor).where(LibroAutor.autor_id == id)
        )
        total = total.one()
        verificar_pagina(pag.page, total, pag.size)
        resultado = await uow.session.exec(
            select(LibroAutor)
            .where(LibroAutor.autor_id == id)
            .options(joinedload(LibroAutor.libro))
            .order_by(LibroAutor.libro_id)
            .offset(pag.offset)
            .limit(pag.limit)
        )
        autorias = resultado.all()
        items = [
            LibroDeAutorRead(
                **LibroRead.model_validate(autoria.libro).model_dump(),
                rol=autoria.rol,
                orden=autoria.orden,
            )
            for autoria in autorias
        ]
        return PaginatedResponse(
            items=items,
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )
