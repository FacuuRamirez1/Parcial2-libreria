"""Contratos de entrada/salida del módulo libros."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from sqlmodel import SQLModel


class LibroAutorCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    autor_id: int
    rol: Literal["autor", "coautor", "traductor", "ilustrador"]
    orden: int = Field(ge=1)


class LibroCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str = Field(max_length=17)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(gt=0)
    stock_inicial: int = Field(ge=0)
    editorial_id: int
    genero_id: int
    autores: list[LibroAutorCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_autores_unicos(self) -> "LibroCreate":
        ids = [autor.autor_id for autor in self.autores]
        if len(ids) != len(set(ids)):
            raise ValueError("No se puede repetir un mismo autor en el mismo libro")
        return self


class LibroUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    titulo: str | None = Field(default=None, max_length=255)
    precio: Decimal | None = Field(default=None)


class ReponerStockRequest(SQLModel):
    model_config = ConfigDict(extra="forbid")

    cantidad: int = Field(gt=0)
    usuario_id: int


class LibroRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    borrado_en: datetime | None = None
    editorial_id: int
    genero_id: int | None = None
