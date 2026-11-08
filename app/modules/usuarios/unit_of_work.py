"""Unit of Work del módulo usuarios: repositorios de usuarios y de clientes sobre una misma sesión.

No crea ni cierra la sesión; confirma al salir del bloque sin excepción y revierte ante excepción.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.unit_of_work import UnitOfWork
from app.modules.clientes.repository import ClienteRepository
from app.modules.usuarios.repository import (
    AsignacionRolRepository,
    EventoSeguridadRepository,
    IntentoAccesoRepository,
    UsuarioRepository,
)


class UsuariosUnitOfWork(UnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.usuarios = UsuarioRepository(session)
        self.asignaciones = AsignacionRolRepository(session)
        self.intentos = IntentoAccesoRepository(session)
        self.eventos = EventoSeguridadRepository(session)
        self.clientes = ClienteRepository(session)
