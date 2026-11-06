"""Lógica de negocio del módulo libros."""

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, paginar
from app.core.unit_of_work import UnitOfWork
from app.modules.libros.models import Libro, LibroAutor, MovimientoStock
from app.modules.libros.repository import LibroRepository
from app.modules.libros.schemas import LibroCreate, LibroRead, LibroUpdate


async def _get_libro(session: SessionDep, id: int) -> Libro:
    repo = LibroRepository(session, Libro)
    libro = await repo.get_by_id(id)
    if libro is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Libro no encontrado")
    return libro


async def crear_libro(session: SessionDep, data: LibroCreate) -> LibroRead:
    """Crea el libro y sus autorías en una única transacción.

    No consulta de antemano editorial, género ni autor: si la base rechaza el
    ISBN, una clave foránea o un CHECK, el `IntegrityError` sale del bloque,
    `UnitOfWork` revierte y el handler global responde 409.
    """
    repo = LibroRepository(session, Libro)
    libro = Libro(
        isbn=data.isbn,
        titulo=data.titulo,
        precio=data.precio,
        stock=data.stock_inicial,
        editorial_id=data.editorial_id,
        genero_id=data.genero_id,
    )
    async with UnitOfWork(session):
        await repo.add(libro)  # flush: asigna libro.id
        for autor in data.autores:
            session.add(
                LibroAutor(
                    libro_id=libro.id,
                    autor_id=autor.autor_id,
                    rol=autor.rol,
                    orden=autor.orden,
                )
            )
        await session.flush()
    return LibroRead.model_validate(libro)


async def listar_libros(
    session: SessionDep,
    page: int,
    size: int,
    titulo: str | None = None,
    genero_id: int | None = None,
) -> PaginatedResponse[LibroRead]:
    repo = LibroRepository(session, Libro)
    total = await repo.count_filtrado(titulo=titulo, genero_id=genero_id)
    offset = (page - 1) * size
    items = await repo.get_all_filtrado(
        titulo=titulo,
        genero_id=genero_id,
        offset=offset,
        limit=size,
    )
    return paginar(
        [LibroRead.model_validate(i) for i in items],
        total,
        page,
        size,
    )


async def obtener_libro(session: SessionDep, id: int) -> LibroRead:
    libro = await _get_libro(session, id)
    return LibroRead.model_validate(libro)


async def actualizar_libro(
    session: SessionDep, id: int, data: LibroUpdate
) -> LibroRead:
    libro = await _get_libro(session, id)
    repo = LibroRepository(session, Libro)
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(libro, key, value)
    await repo.update(libro)
    await session.commit()
    return LibroRead.model_validate(libro)


async def soft_delete_libro(session: SessionDep, id: int) -> None:
    repo = LibroRepository(session, Libro)
    libro = await repo.get_by_id_including_deleted(id)
    if libro is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Libro no encontrado")
    await repo.soft_delete(libro)
    await session.commit()


async def reponer_stock(
    session: SessionDep, id: int, cantidad: int, usuario_id: int
) -> LibroRead:
    repo = LibroRepository(session, Libro)
    libro = await repo.get_by_id(id)
    if libro is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Libro no encontrado")
    libro.stock = libro.stock + cantidad
    await repo.update(libro)
    movimiento = MovimientoStock(
        libro_id=libro.id,
        usuario_id=usuario_id,
        cantidad=cantidad,
        motivo="reposicion_stock",
    )
    session.add(movimiento)
    await session.commit()
    return LibroRead.model_validate(libro)
