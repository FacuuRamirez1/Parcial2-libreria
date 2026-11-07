"""Lógica de negocio del módulo generos (recibe la sesión como parámetro)."""

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.core.database import SessionDep
from app.core.paginacion import Paginacion
from app.modules.generos.models import Genero
from app.modules.generos.schemas import GeneroCreate, GeneroRead, GeneroUpdate
from app.modules.libros.models import Libro
from app.modules.libros.schemas import LibroRead

MENSAJE_NO_ENCONTRADO = "Género no encontrado"


async def _confirmar(session: SessionDep) -> None:
    """Commit; si la base rechaza la escritura se revierte y el handler responde 409."""
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise


async def _obtener(session: SessionDep, id: int) -> Genero:
    genero = await session.get(Genero, id)
    if genero is None:
        raise HTTPException(status_code=404, detail=MENSAJE_NO_ENCONTRADO)
    return genero


async def crear_genero(session: SessionDep, data: GeneroCreate) -> GeneroRead:
    genero = Genero(**data.model_dump())
    session.add(genero)
    await _confirmar(session)
    return GeneroRead.model_validate(genero)


async def listar_generos(session: SessionDep, pag: Paginacion) -> list[GeneroRead]:
    resultado = await session.exec(
        select(Genero).order_by(Genero.id).offset(pag.offset).limit(pag.limit)
    )
    return [GeneroRead.model_validate(g) for g in resultado.all()]


async def obtener_genero(session: SessionDep, id: int) -> GeneroRead:
    return GeneroRead.model_validate(await _obtener(session, id))


async def actualizar_genero(
    session: SessionDep, id: int, data: GeneroUpdate
) -> GeneroRead:
    genero = await _obtener(session, id)
    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(genero, campo, valor)
    await _confirmar(session)
    return GeneroRead.model_validate(genero)


async def listar_libros_de_genero(
    session: SessionDep, id: int, pag: Paginacion
) -> list[LibroRead]:
    await _obtener(session, id)
    resultado = await session.exec(
        select(Libro)
        .where(Libro.genero_id == id)
        .order_by(Libro.id)
        .offset(pag.offset)
        .limit(pag.limit)
    )
    return [LibroRead.model_validate(libro) for libro in resultado.all()]
