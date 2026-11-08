"""Contratos de entrada/salida del módulo autores."""

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class AutorCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(max_length=120)
    nacionalidad: str = Field(max_length=60)


class AutorUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=120)
    nacionalidad: str | None = Field(default=None, max_length=60)


class AutorRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    nacionalidad: str
