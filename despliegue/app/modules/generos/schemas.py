"""Contratos de entrada/salida del módulo generos."""

from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class GeneroCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(max_length=60)


class GeneroUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str | None = Field(default=None, max_length=60)


class GeneroRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
