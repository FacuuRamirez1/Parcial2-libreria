"""Lógica de negocio del módulo editoriales (recibe la sesión como parámetro)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
from app.modules.editoriales.models import Editorial
from app.modules.editoriales.schemas import EditorialCreate, EditorialRead, EditorialUpdate
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead

MENSAJE_NO_ENCONTRADA = "Editorial no encontrada"


async def _confirmar(session: SessionDep) -> None:
    """Commit; si la base rechaza la escritura se revierte y el handler responde 409."""
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def _obtener(session: SessionDep, id: int) -> Editorial:
    editorial = await session.get(Editorial, id)
    if editorial is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADA)
    return editorial


async def crear_editorial(session: SessionDep, data: EditorialCreate) -> EditorialRead:
    editorial = Editorial(**data.model_dump())
    session.add(editorial)
    await _confirmar(session)
    return EditorialRead.model_validate(editorial)


async def listar_editoriales(
    session: SessionDep, pag: Paginacion
) -> list[EditorialRead]:
    resultado = await session.exec(
        select(Editorial).order_by(Editorial.id).offset(pag.offset).limit(pag.limit)
    )
    return [EditorialRead.model_validate(e) for e in resultado.all()]


async def obtener_editorial(session: SessionDep, id: int) -> EditorialRead:
    return EditorialRead.model_validate(await _obtener(session, id))


async def actualizar_editorial(
    session: SessionDep, id: int, data: EditorialUpdate
) -> EditorialRead:
    editorial = await _obtener(session, id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(editorial, campo, valor)
    await _confirmar(session)
    return EditorialRead.model_validate(editorial)


async def listar_libros_de_editorial(
    session: SessionDep, id: int, pag: Paginacion
) -> list[LibroRead]:
    await _obtener(session, id)
    resultado = await session.exec(
        select(Libro)
        .where(Libro.editorial_id == id)
        .order_by(Libro.id)
        .offset(pag.offset)
        .limit(pag.limit)
    )
    return [LibroRead.model_validate(libro) for libro in resultado.all()]
