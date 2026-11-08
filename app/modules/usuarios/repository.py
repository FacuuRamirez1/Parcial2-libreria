"""Repositorios del módulo usuarios.

Todos heredan de BaseRepository y NO hacen commit: confirma solo el Unit of Work.
La única excepción del sistema es `RegistroIntentosPropio` (ver su comentario).
"""

from datetime import UTC, datetime

from sqlalchemy import func, or_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlmodel import select

from app.core.repository import BaseRepository
from app.modules.usuarios.models import (
    AsignacionRol,
    EventoSeguridad,
    IntentoAcceso,
    Usuario,
)


# Marca de "nunca hubo un éxito": anterior a cualquier intento real.
_SIN_EXITO = datetime(1900, 1, 1, tzinfo=UTC)


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Usuario)

    async def get_by_email(self, email: str) -> Usuario | None:
        resultado = await self.session.exec(select(Usuario).where(Usuario.email == email))
        return resultado.first()


class AsignacionRolRepository(BaseRepository[AsignacionRol]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AsignacionRol)

    def _consulta_roles_vigentes(self, usuario_id: int, ahora: datetime):
        return (
            select(AsignacionRol.rol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .where(AsignacionRol.revocada_en.is_(None))
            .where(or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > ahora))
            .order_by(AsignacionRol.rol)
        )

    async def roles_vigentes(self, usuario_id: int, ahora: datetime) -> list[str]:
        """Roles no revocados y sin vencer a `ahora` (D-10)."""
        resultado = await self.session.exec(self._consulta_roles_vigentes(usuario_id, ahora))
        return list(resultado.all())

    async def get_abierta(self, usuario_id: int, rol: str) -> AsignacionRol | None:
        """La asignación abierta (`revocada_en IS NULL`) de ese rol, vigente o vencida.

        A lo sumo una por el índice único parcial ix_asignacion_rol_abierta (su garante)."""
        resultado = await self.session.exec(
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .where(AsignacionRol.rol == rol)
            .where(AsignacionRol.revocada_en.is_(None))
        )
        return resultado.first()

    async def contar_admins_vigentes(self, ahora: datetime) -> int:
        """Usuarios ACTIVOS con ADMIN vigente (no revocado y sin vencer a `ahora`). Una sola
        consulta con JOIN a `usuario` para mirar `activo`; cuenta usuarios, no asignaciones."""
        resultado = await self.session.exec(
            select(func.count(func.distinct(AsignacionRol.usuario_id)))
            .join(Usuario, Usuario.id == AsignacionRol.usuario_id)
            .where(AsignacionRol.rol == "ADMIN")
            .where(Usuario.activo.is_(True))
            .where(AsignacionRol.revocada_en.is_(None))
            .where(or_(AsignacionRol.vence_en.is_(None), AsignacionRol.vence_en > ahora))
        )
        return resultado.one()

    async def listar_de_usuario(self, usuario_id: int) -> list[AsignacionRol]:
        """Todo el historial del usuario (vigentes, vencidas y revocadas), por `desde` e id."""
        resultado = await self.session.exec(
            select(AsignacionRol)
            .where(AsignacionRol.usuario_id == usuario_id)
            .order_by(AsignacionRol.desde, AsignacionRol.id)
        )
        return list(resultado.all())


class IntentoAccesoRepository(BaseRepository[IntentoAcceso]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, IntentoAcceso)

    def _consulta_fallos_recientes(self, email: str, ip: str, desde: datetime):
        ultimo_exito = (
            select(func.coalesce(func.max(IntentoAcceso.cuando), _SIN_EXITO))
            .where(IntentoAcceso.email == email)
            .where(IntentoAcceso.ip == ip)
            .where(IntentoAcceso.exito.is_(True))
            .scalar_subquery()
        )
        return (
            select(func.count(), func.min(IntentoAcceso.cuando))
            .where(IntentoAcceso.email == email)
            .where(IntentoAcceso.ip == ip)
            .where(IntentoAcceso.exito.is_(False))
            .where(IntentoAcceso.cuando > desde)
            .where(IntentoAcceso.cuando > ultimo_exito)
        )

    async def contar_fallos_recientes(
        self, email: str, ip: str, desde: datetime
    ) -> tuple[int, datetime | None]:
        """Cantidad y fecha del más antiguo de los fallos de (email, ip) desde `desde`
        y posteriores al último éxito de ese par. Una sola consulta (D-06)."""
        resultado = await self.session.exec(self._consulta_fallos_recientes(email, ip, desde))
        cantidad, mas_antiguo = resultado.one()
        return cantidad, mas_antiguo


class EventoSeguridadRepository(BaseRepository[EventoSeguridad]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, EventoSeguridad)

    async def listar_recientes(self, offset: int, limit: int) -> list[EventoSeguridad]:
        """Una página del historial, del más reciente al más antiguo (`cuando DESC, id DESC`)."""
        resultado = await self.session.exec(
            select(EventoSeguridad)
            .order_by(EventoSeguridad.cuando.desc(), EventoSeguridad.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(resultado.all())


class RegistroIntentosPropio:
    """Escribe `intento_acceso` en una sesión y una transacción PROPIAS.

    Qué hace distinto: es la única escritura del sistema que NO usa el Unit of Work
    de la petición; abre su propia sesión desde la fábrica de la aplicación, su
    propia transacción, y la confirma SIEMPRE, salga como salga la petición.

    Por qué no puede compartir la transacción de la petición: el fallo que se quiere
    contar es justamente el que termina en 401 y revierte la transacción de la
    petición; si compartiera esa transacción, el intento fallido desaparecería con
    el rollback y el límite de intentos nunca se alcanzaría.

    Costo: deja filas aunque la petición falle (es lo buscado), y toma una segunda
    conexión del pool durante el login (la de la petición ya se liberó antes de bcrypt).
    """

    def __init__(self, fabrica_sesiones: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica_sesiones

    async def anotar(self, email: str, ip: str, exito: bool) -> None:
        async with self._fabrica() as sesion:
            async with sesion.begin():  # confirma al salir del bloque; revierte solo si esta escritura falla
                sesion.add(IntentoAcceso(email=email, ip=ip, exito=exito))
