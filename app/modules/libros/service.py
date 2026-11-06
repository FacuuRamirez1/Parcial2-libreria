"""Lógica de negocio del módulo libros."""

from app.core.database import SessionDep
from app.core.paginacion import PaginatedResponse, paginar
from app.modules.libros.models import Libro
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
    repo = LibroRepository(session, Libro)
    libro = Libro(
        isbn=data.isbn,
        titulo=data.titulo,
        precio=data.precio,
        stock=data.stock_inicial,
        editorial_id=data.editorial_id,
        genero_id=data.genero_id,
    )
    await repo.add(libro)
    await session.commit()
    return LibroRead.model_validate(libro)


async def listar_libros(
    session: SessionDep, page: int, size: int
) -> PaginatedResponse[LibroRead]:
    repo = LibroRepository(session, Libro)
    total = await repo.count()
    offset = (page - 1) * size
    items = await repo.get_all(offset=offset, limit=size)
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


async def reponer_stock(session: SessionDep, id: int, cantidad: int) -> LibroRead:
    repo = LibroRepository(session, Libro)
    libro = await repo.get_by_id(id)
    if libro is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Libro no encontrado")
    libro.stock = libro.stock + cantidad
    await repo.update(libro)
    await session.commit()
    return LibroRead.model_validate(libro)
