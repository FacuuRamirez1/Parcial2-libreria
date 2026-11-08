"""Tablas del módulo usuarios: usuario, asignacion_rol, intento_acceso y evento_seguridad."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.sql.sqltypes import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import MovimientoStock


def _ahora() -> datetime:
    return datetime.now(UTC)


class Usuario(SQLModel, table=True):
    """Persona que inicia sesión. Los roles viven en `asignacion_rol`, no acá."""

    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, unique=True)
    nombre: str = Field(max_length=120)
    password_hash: str = Field(max_length=255)
    activo: bool = Field(default=True, sa_column_kwargs={"server_default": text("true")})
    debe_cambiar_password: bool = Field(
        default=False, sa_column_kwargs={"server_default": text("false")}
    )

    asignaciones: list["AsignacionRol"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "AsignacionRol.usuario_id",
        },
    )
    asignaciones_otorgadas: list["AsignacionRol"] = Relationship(
        back_populates="otorgante",
        sa_relationship_kwargs={
            "lazy": "raise",
            "foreign_keys": "AsignacionRol.otorgada_por",
        },
    )
    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise", "uselist": False},
    )
    movimientos: list["MovimientoStock"] = Relationship(
        back_populates="usuario", sa_relationship_kwargs={"lazy": "raise"}
    )


class AsignacionRol(SQLModel, table=True):
    """Rol otorgado a un usuario; una sola asignación abierta por (usuario, rol)."""

    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint("rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name="rol_valido"),
        Index(
            "ix_asignacion_rol_abierta",
            "usuario_id",
            "rol",
            unique=True,
            postgresql_where=text("revocada_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    rol: str = Field(max_length=20)
    desde: datetime = Field(
        default_factory=_ahora,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )
    vence_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    revocada_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    otorgada_por: int | None = Field(default=None, foreign_key="usuario.id", index=True)

    usuario: "Usuario" = Relationship(
        back_populates="asignaciones",
        sa_relationship_kwargs={"lazy": "raise", "foreign_keys": "AsignacionRol.usuario_id"},
    )
    otorgante: Optional["Usuario"] = Relationship(
        back_populates="asignaciones_otorgadas",
        sa_relationship_kwargs={"lazy": "raise", "foreign_keys": "AsignacionRol.otorgada_por"},
    )


class IntentoAcceso(SQLModel, table=True):
    """Intento de login; sin FK porque el correo puede no existir."""

    __tablename__ = "intento_acceso"
    __table_args__ = (Index("ix_intento_acceso_email_ip_cuando", "email", "ip", "cuando"),)

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=_ahora,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )
    email: str = Field(max_length=254)
    ip: str = Field(max_length=45)
    exito: bool


class EventoSeguridad(SQLModel, table=True):
    """Historial de seguridad; `actor` es texto (correo o SISTEMA), no FK."""

    __tablename__ = "evento_seguridad"

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        default_factory=_ahora,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )
    actor: str = Field(max_length=254)
    accion: str = Field(max_length=255)
