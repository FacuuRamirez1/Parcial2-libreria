"""Unit of Work del módulo libros.

Compone LibroRepository sobre la misma sesión. No crea ni cierra la sesión;
confirma al salir del bloque sin excepción y revierte ante excepción.
"""

from app.core.unit_of_work import UnitOfWork
from app.modules.libros.repository import LibroRepository


class LibrosUnitOfWork(UnitOfWork):
    def __init__(self, session) -> None:
        super().__init__(session)
        self.libros = LibroRepository(session)
