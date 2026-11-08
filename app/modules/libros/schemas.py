"""Contratos de entrada/salida del módulo libros."""

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import ConfigDict, Field, model_validator
from sqlmodel import SQLModel

from app.modules.autores.schemas import AutorRead
from app.modules.editoriales.schemas import EditorialRead
from app.modules.generos.schemas import GeneroRead


class LibroAutorCreate(SQLModel):
    """Datos de la relación: el id del autor existente más el rol y el orden."""

    model_config = ConfigDict(extra="forbid")

    autor_id: int
    rol: Literal["autor", "coautor", "traductor", "ilustrador"]
    orden: int = Field(ge=1)


class LibroCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str = Field(max_length=17)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    stock_inicial: int = Field(ge=0)
    editorial_id: int
    genero_id: int | None = None
    autores: list[LibroAutorCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validar_autores_unicos(self) -> "LibroCreate":
        ids = [autor.autor_id for autor in self.autores]
        if len(ids) != len(set(ids)):
            raise ValueError("No se puede repetir un mismo autor en el mismo libro")
        return self


class LibroUpdate(SQLModel):
    model_config = ConfigDict(extra="forbid")

    isbn: str | None = Field(default=None, max_length=17)
    titulo: str | None = Field(default=None, max_length=255)
    precio: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    editorial_id: int | None = None
    genero_id: int | None = None


class ReposicionIn(SQLModel):
    """Reposición de stock: solo la cantidad positiva (extra="forbid")."""

    model_config = ConfigDict(extra="forbid")

    cantidad: int = Field(gt=0)


class MovimientoStockRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    libro_id: int
    venta_id: int | None = None
    usuario_id: int
    cantidad: int
    motivo: str
    cuando: datetime


class LibroRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    precio: Decimal
    stock: int
    editorial_id: int
    genero_id: int | None = None


class LibroListaRead(LibroRead):
    """Libro con su editorial y su género (listado)."""

    editorial: EditorialRead
    genero: GeneroRead | None = None


class LibroAutorRead(SQLModel):
    model_config = ConfigDict(from_attributes=True)

    autor: AutorRead
    rol: str
    orden: int


class LibroDetalleRead(LibroListaRead):
    """Libro con editorial, género y autores (con rol y orden)."""

    autores: list[LibroAutorRead] = Field(default_factory=list)


class LibroDeAutorRead(LibroRead):
    """Libro visto desde un autor: incluye el rol y el orden de esa autoría."""

    rol: str
    orden: int
