"""Tablas del módulo clientes: cliente y perfil_cliente."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import Venta


class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=120)
    email: str = Field(max_length=254, unique=True)
    # El UNIQUE ya cubre las búsquedas por usuario_id: no lleva index=True.
    usuario_id: int | None = Field(default=None, foreign_key="usuario.id", unique=True)

    usuario: Optional["Usuario"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={"lazy": "raise", "uselist": False},
    )

    perfil: Optional["PerfilCliente"] = Relationship(
        back_populates="cliente",
        sa_relationship_kwargs={
            "lazy": "raise",
            "uselist": False,
            "cascade": "all, delete-orphan",
        },
    )
    ventas: list["Venta"] = Relationship(
        back_populates="cliente", sa_relationship_kwargs={"lazy": "raise"}
    )


class PerfilCliente(SQLModel, table=True):
    __tablename__ = "perfil_cliente"

    id: int | None = Field(default=None, primary_key=True)
    cliente_id: int = Field(foreign_key="cliente.id", unique=True)
    telefono: str = Field(max_length=30)
    direccion: str = Field(max_length=255)

    cliente: "Cliente" = Relationship(
        back_populates="perfil", sa_relationship_kwargs={"lazy": "raise"}
    )
