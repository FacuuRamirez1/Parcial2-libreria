"""Contratos de entrada/salida del módulo libros."""

from datetime import datetime
from decimal import Decimal
from pydantic import ConfigDict, Field
from sqlmodel import SQLModel


class LibroCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str = Field(max_length=17)
    titulo: str = Field(max_length=255)
    precio: Decimal
    stock_inicial: int
    editorial_id: int
    genero_id: int | None = Field(default=None)


class LibroUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str | None = Field(default=None, max_length=17)
    titulo: str | None = Field(default=None, max_length=255)
    precio: Decimal | None = Field(default=None)
    editorial_id: int | None = Field(default=None)
    genero_id: int | None = Field(default=None)


class ReponerStockRequest(SQLModel):
    model_config = ConfigDict(extra="forbid")

    cantidad: int = Field(gt=0)


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
