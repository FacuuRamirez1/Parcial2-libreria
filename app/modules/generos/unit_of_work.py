"""Unit of Work del módulo generos.

Compone GeneroRepository sobre la misma sesión. No crea ni cierra la sesión;
confirma al salir del bloque sin excepción y revierte ante excepción.
"""

from app.core.unit_of_work import UnitOfWork
from app.modules.generos.repository import GeneroRepository


class GenerosUnitOfWork(UnitOfWork):
    def __init__(self, session) -> None:
        super().__init__(session)
        self.generos = GeneroRepository(session)
