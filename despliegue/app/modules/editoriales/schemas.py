"""Contratos de entrada/salida del módulo editoriales."""

from decimal import Decimal  # noqa: F401  (reservado para coherencia de módulos)
from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class EditorialCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(max_length=120)
    pais: str = Field(max_length=60)


class EditorialUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=120)
    pais: str | None = Field(default=None, max_length=60)


class EditorialRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    pais: str
