"""Unit of Work del módulo clientes.

Compone ClienteRepository sobre la misma sesión. No crea ni cierra la sesión;
confirma al salir del bloque sin excepción y revierte ante excepción.
"""

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository


class ClientesUnitOfWork(UnitOfWork):
    def __init__(self, session) -> None:
        super().__init__(session)
        self.clientes = ClienteRepository(session)
