"""Lógica de negocio del módulo autores (recibe la sesión como parámetro)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
from app.modules.autores.models import Autor
from app.modules.autores.schemas import AutorCreate, AutorRead, AutorUpdate
from app.modules.libros.models import LibroAutor
from app.modules.libros.schemas import LibroDeAutorRead, LibroRead

MENSAJE_NO_ENCONTRADO = "Autor no encontrado"


async def _confirmar(session: SessionDep) -> None:
    """Commit; si la base rechaza la escritura se revierte y el handler responde 409."""
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def _obtener(session: SessionDep, id: int) -> Autor:
    autor = await session.get(Autor, id)
    if autor is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return autor


async def crear_autor(session: SessionDep, data: AutorCreate) -> AutorRead:
    autor = Autor(**data.model_dump())
    session.add(autor)
    await _confirmar(session)
    return AutorRead.model_validate(autor)


async def listar_autores(session: SessionDep, pag: Paginacion) -> list[AutorRead]:
    resultado = await session.exec(
        select(Autor).order_by(Autor.id).offset(pag.offset).limit(pag.limit)
    )
    return [AutorRead.model_validate(a) for a in resultado.all()]


async def obtener_autor(session: SessionDep, id: int) -> AutorRead:
    return AutorRead.model_validate(await _obtener(session, id))


async def actualizar_autor(
    session: SessionDep, id: int, data: AutorUpdate
) -> AutorRead:
    autor = await _obtener(session, id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(autor, campo, valor)
    await _confirmar(session)
    return AutorRead.model_validate(autor)


async def listar_libros_de_autor(
    session: SessionDep, id: int, pag: Paginacion
) -> list[LibroDeAutorRead]:
    """Libros del autor con el rol y el orden de cada autoría (una sola consulta)."""
    await _obtener(session, id)
    resultado = await session.exec(
        select(LibroAutor)
        .where(LibroAutor.autor_id == id)
        .options(joinedload(LibroAutor.libro))
        .order_by(LibroAutor.libro_id)
        .offset(pag.offset)
        .limit(pag.limit)
    )
    return [
        LibroDeAutorRead(
            **LibroRead.model_validate(autoria.libro).model_dump(),
            rol=autoria.rol,
            orden=autoria.orden,
        )
        for autoria in resultado.all()
    ]
