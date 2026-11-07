"""Lógica de negocio del módulo libros (recibe la sesión como parámetro)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
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

MENSAJE_NO_ENCONTRADO = "Libro no encontrado"


# Carga anticipada declarada en la misma consulta: joinedload para relaciones a uno,
# selectinload para la colección de autorías (y joinedload del autor dentro de ella).
# Son funciones y no constantes para no configurar los mappers al importar el módulo.
def _opciones_lista() -> tuple:
    return (joinedload(Libro.editorial), joinedload(Libro.genero))


def _opciones_detalle() -> tuple:
    return (
        *_opciones_lista(),
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


async def _confirmar(session: SessionDep) -> None:
    """Commit; si la base rechaza la escritura se revierte y el handler responde 409."""
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def crear_libro(session: SessionDep, data: LibroCreate) -> LibroDetalleRead:
    """Crea el libro y sus autorías en una única transacción.

    No consulta de antemano editorial, género ni autor: si la base rechaza el ISBN,
    una clave foránea o un CHECK, se revierte y el handler global responde 409.
    """
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
    session.add(libro)
    await _confirmar(session)
    return await obtener_libro(session, libro.id)


async def listar_libros(
    session: SessionDep,
    pag: Paginacion,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> list[LibroListaRead]:
    """Una sola consulta: editorial y género llegan con joinedload."""
    consulta = select(Libro).options(*_opciones_lista())
    if titulo:
        # El texto viaja como parámetro ligado; `autoescape` neutraliza % y _.
        consulta = consulta.where(Libro.titulo.icontains(titulo, autoescape=True))
    if genero_id is not None:
        consulta = consulta.where(Libro.genero_id == genero_id)
    resultado = await session.exec(
        consulta.order_by(Libro.id).offset(pag.offset).limit(pag.limit)
    )
    return [_a_lista(libro) for libro in resultado.all()]


async def obtener_libro(session: SessionDep, id: int) -> LibroDetalleRead:
    """Dos consultas fijas, sin importar cuántos autores tenga el libro."""
    resultado = await session.exec(
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
    session: SessionDep, id: int, data: LibroUpdate
) -> LibroDetalleRead:
    libro = await session.get(Libro, id)
    if libro is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(libro, campo, valor)
    await _confirmar(session)
    return await obtener_libro(session, id)
