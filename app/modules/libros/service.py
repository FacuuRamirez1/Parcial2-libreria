"""Lógica de negocio del módulo libros (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.libros y
uow.session para consultas cruzadas (alta con autorías, detalle, relación).
"""

from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload, selectinload

from app.core.paginacion import Paginacion, PaginatedResponse, calcular_paginas, verificar_pagina
from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.schemas import (
    LibroAutorRead,
    LibroCreate,
    LibroDetalleRead,
    LibroListaRead,
    LibroRead,
    LibroUpdate,
)
from app.modules.libros.unit_of_work import LibrosUnitOfWork

MENSAJE_NO_ENCONTRADO = "Libro no encontrado"


def _opciones_detalle() -> tuple:
    return (
        joinedload(Libro.editorial),
        joinedload(Libro.genero),
        selectinload(Libro.autorias).joinedload(LibroAutor.autor),
    )


def _a_lista(libro: Libro) -> LibroListaRead:
    return LibroListaRead(
        **LibroRead.model_validate(libro).model_dump(),
        editorial=EditorialRead.model_validate(libro.editorial),
        genero=GeneroRead.model_validate(libro.genero) if libro.genero else None,
    )


def _a_detalle(libro: Libro) -> LibroDetalleRead:
    return LibroDetalleRead(
        **_a_lista(libro).model_dump(),
        autores=[LibroAutorRead.model_validate(a) for a in libro.autorias],
    )


async def crear_libro(uow: LibrosUnitOfWork, data: LibroCreate) -> LibroDetalleRead:
    """Crea el libro y sus autorías en una única transacción (commit en el UoW).

    No consulta de antemano editorial, género ni autor: si la base rechaza el
    ISBN, una clave foránea o un CHECK, se revierte y el handler global
    responde 409.
    """
    async with uow:
        libro = Libro(
            isbn=data.isbn,
            titulo=data.titulo,
            precio=data.precio,
            stock=data.stock,
            editorial_id=data.editorial_id,
            genero_id=data.genero_id,
            autorias=[
                LibroAutor(autor_id=a.autor_id, rol=a.rol, orden=a.orden)
                for a in data.autores
            ],
        )
        await uow.libros.add(libro)
        return await _obtener_detalle(uow, libro.id)


async def listar_libros(
    uow: LibrosUnitOfWork,
    pag: Paginacion,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> PaginatedResponse[LibroListaRead]:
    async with uow:
        total = await uow.libros.count_filtrado(titulo=titulo, genero_id=genero_id)
        verificar_pagina(pag.page, total, pag.size)
        items = await uow.libros.get_all_filtrado(
            titulo=titulo, genero_id=genero_id, offset=pag.offset, limit=pag.limit
        )
        return PaginatedResponse(
            items=[_a_lista(libro) for libro in items],
            total=total,
            page=pag.page,
            size=pag.size,
            pages=calcular_paginas(total, pag.size),
        )


async def obtener_libro(uow: LibrosUnitOfWork, id: int) -> LibroDetalleRead:
    async with uow:
        return await _obtener_detalle(uow, id)


async def _obtener_detalle(uow: LibrosUnitOfWork, id: int) -> LibroDetalleRead:
    resultado = await uow.session.exec(
        select(Libro)
        .where(Libro.id == id)
        .options(*_opciones_detalle())
        .execution_options(populate_existing=True)
    )
    libro = resultado.first()
    if libro is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return _a_detalle(libro)


async def actualizar_libro(
    uow: LibrosUnitOfWork, id: int, data: LibroUpdate
) -> LibroDetalleRead:
    async with uow:
        libro = await uow.session.get(Libro, id)
        if libro is None:
            raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(libro, campo, valor)
        await uow.libros.update(libro)
        return await _obtener_detalle(uow, id)
