"""Lógica de negocio del módulo generos (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.repositorios.
"""

from fastapi import HTTPException
from sqlmodel import select

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.generos.unit_of_work import GenerosUnitOfWork
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead

MENSAJE_NO_ENCONTRADO = "Género no encontrado"


async def _obtener(uow: GenerosUnitOfWork, id: int) -> Genero:
    genero = await uow.generos.get_by_id(id)
    if genero is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return genero


async def crear_genero(uow: GenerosUnitOfWork, data: GeneroCreate) -> GeneroRead:
    async with uow:
        genero = Genero(**data.model_dump())
        await uow.generos.add(genero)
        return GeneroRead.model_validate(genero)


async def listar_generos(uow: GenerosUnitOfWork, pag: Paginacion) -> PaginatedResponse[GeneroRead]:
    async with uow:
        total = await uow.generos.count()
        verificar_pagina(pag.page, pag.size, total)
        items = await uow.generos.get_all(offset=pag.offset, limit=pag.limit)
        return PaginatedResponse(
            items=[GeneroRead.model_validate(g) for g in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )


async def obtener_genero(uow: GenerosUnitOfWork, id: int) -> GeneroRead:
    async with uow:
        return GeneroRead.model_validate(await _obtener(uow, id))


async def actualizar_genero(
    uow: GenerosUnitOfWork, id: int, data: GeneroUpdate
) -> GeneroRead:
    async with uow:
        genero = await _obtener(uow, id)
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(genero, campo, valor)
        await uow.generos.update(genero)
        return GeneroRead.model_validate(genero)


async def listar_libros_de_genero(
    uow: GenerosUnitOfWork, id: int, pag: Paginacion
) -> PaginatedResponse[LibroRead]:
    async with uow:
        await _obtener(uow, id)
        from sqlalchemy import func

        total = await uow.session.exec(
            select(func.count()).select_from(Libro).where(Libro.genero_id == id)
        )
        total = total.one()
        verificar_pagina(pag.page, pag.size, total)
        resultado = await uow.session.exec(
            select(Libro)
            .where(Libro.genero_id == id)
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
