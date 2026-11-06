"""Tablas del módulo usuarios: usuario, asignacion_rol, intento_acceso, evento_seguridad."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.sql.sqltypes import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.clientes.models import Cliente
    from app.modules.libros.models import MovimientoStock


class Usuario(SQLModel, table=True):
    __tablename__ = "usuario"

    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(max_length=254, unique=True)
    nombre: str = Field(max_length=120)
    password_hash: str = Field(max_length=255)
    activo: bool = Field(default=True)
    debe_cambiar_password: bool = Field(default=False)

    cliente: Optional["Cliente"] = Relationship(
        back_populates="usuario",
        sa_relationship_kwargs={"lazy": "raise", "uselist": False},
    )
    asignaciones_rol: list["AsignacionRol"] = Relationship(
        back_populates="usuario", sa_relationship_kwargs={"lazy": "raise"}
    )
    movimientos_stock: list["MovimientoStock"] = Relationship(
        back_populates="usuario", sa_relationship_kwargs={"lazy": "raise"}
    )


class AsignacionRol(SQLModel, table=True):
    __tablename__ = "asignacion_rol"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('ADMIN', 'VENDEDOR', 'CLIENTE')", name="ck_asignacion_rol_valido"
        ),
        Index(
            "uq_asignacion_rol_activa",
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
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    vence_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    revocada_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))
    otorgada_por: str | None = Field(default=None, max_length=255)

    usuario: "Usuario" = Relationship(
        back_populates="asignaciones_rol", sa_relationship_kwargs={"lazy": "raise"}
    )


class IntentoAcceso(SQLModel, table=True):
    __tablename__ = "intento_acceso"
    __table_args__ = (
        Index(
            "ix_intento_acceso_email_ip_cuando",
            "email",
            "ip",
            "cuando",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    email: str = Field(max_length=254)
    ip: str = Field(max_length=45)
    exito: bool


class EventoSeguridad(SQLModel, table=True):
    __tablename__ = "evento_seguridad"

    id: int | None = Field(default=None, primary_key=True)
    cuando: datetime = Field(
        sa_type=DateTime(timezone=True), default_factory=lambda: datetime.now(UTC)
    )
    actor: str = Field(max_length=254)
    accion: str = Field(max_length=100)
