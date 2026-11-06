"""Contratos de entrada/salida del módulo clientes."""

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class ClienteCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(max_length=120)
    email: str = Field(max_length=254)
    usuario_id: int | None = Field(default=None)


class ClienteUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=120)
    email: str | None = Field(default=None, max_length=254)
    usuario_id: int | None = Field(default=None)


class ClienteRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    email: str
    usuario_id: int | None = None


class PerfilClienteCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    telefono: str = Field(max_length=30)
    direccion: str = Field(max_length=255)
    cliente_id: int | None = Field(default=None)


class PerfilClienteRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    telefono: str
    direccion: str
    cliente_id: int
