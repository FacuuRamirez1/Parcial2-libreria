"""Lógica de negocio del módulo libros (recibe el UnitOfWork).

Nunca construye el UoW, nunca llama session.commit(); usa uow.libros y
uow.session para consultas cruzadas (alta con autorías, detalle, relación).
El stock solo cambia por `app.modules.libros.stock.registrar_movimiento`.
"""

from fastapi import HTTPException

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
    MovimientoStockRead,
)
from app.modules.libros.stock import registrar_movimiento
from app.modules.libros.unit_of_work import LibrosUnitOfWork

MENSAJE_NO_ENCONTRADO = "Libro no encontrado"
MENSAJE_LIBRO_DADO_DE_BAJA = "El libro está dado de baja"


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


async def crear_libro(
    uow: LibrosUnitOfWork, data: LibroCreate, usuario_id: int
) -> LibroDetalleRead:
    """Crea el libro (stock 0) y, si hay stock inicial, su movimiento.

    No consulta de antemano editorial, género ni autor: si la base rechaza el
    ISBN, una clave foránea o un CHECK, se revierte y el handler global
    responde 409. El stock inicial entra por el punto único de movimiento.
    """
    async with uow:
        libro = Libro(
            isbn=data.isbn,
            titulo=data.titulo,
            precio=data.precio,
            stock=0,
            editorial_id=data.editorial_id,
            genero_id=data.genero_id,
            autorias=[
                LibroAutor(autor_id=a.autor_id, rol=a.rol, orden=a.orden)
                for a in data.autores
            ],
        )
        await uow.libros.add(libro)
        if data.stock_inicial > 0:
            await registrar_movimiento(
                uow,
                libro=libro,
                cantidad=data.stock_inicial,
                motivo="Stock inicial",
                usuario_id=usuario_id,
            )
        return await _obtener_detalle(uow, libro.id)


async def listar_libros(
    uow: LibrosUnitOfWork,
    pag: Paginacion,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> PaginatedResponse[LibroListaRead]:
    async with uow:
        total = await uow.libros.count_filtrado(titulo=titulo, genero_id=genero_id)
        verificar_pagina(pag.page, pag.size, total)
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
    libro = await uow.libros.get_detalle(id)
    if libro is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return _a_detalle(libro)


async def actualizar_libro(
    uow: LibrosUnitOfWork, id: int, data: LibroUpdate
) -> LibroDetalleRead:
    async with uow:
        libro = await uow.libros.get_by_id(id)
        if libro is None:
            raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
        for campo, valor in data.model_dump(exclude_unset=True).items():
            setattr(libro, campo, valor)
        await uow.libros.update(libro)
        return await _obtener_detalle(uow, id)


async def reponer_libro(
    uow: LibrosUnitOfWork, id: int, cantidad: int, usuario_id: int
) -> LibroDetalleRead:
    """Suma stock y deja su movimiento; 404 si no existe, 409 si está dado de baja."""
    async with uow:
        libro = await uow.libros.get_by_id_including_deleted(id)
        if libro is None:
            raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
        if libro.borrado_en is not None:
            raise HTTPException(status_code=409, detail=MENSAJE_LIBRO_DADO_DE_BAJA)
        await registrar_movimiento(
            uow,
            libro=libro,
            cantidad=cantidad,
            motivo="Reposición",
            usuario_id=usuario_id,
        )
        return await _obtener_detalle(uow, id)


async def listar_movimientos(
    uow: LibrosUnitOfWork, libro_id: int
) -> list[MovimientoStockRead]:
    """Historial ordenado por id; incluye los movimientos de un libro dado de baja."""
    async with uow:
        libro = await uow.libros.get_by_id_including_deleted(libro_id)
        if libro is None:
            raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
        movimientos = await uow.movimientos.listar_de_libro(libro_id)
        return [MovimientoStockRead.model_validate(m) for m in movimientos]


async def baja_libro(uow: LibrosUnitOfWork, id: int) -> None:
    """Baja lógica: marca borrado_en sin borrar la fila (404 si ya está dada de baja)."""
    async with uow:
        libro = await uow.libros.get_by_id(id)
        if libro is None:
            raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
        await uow.libros.soft_delete(libro)
