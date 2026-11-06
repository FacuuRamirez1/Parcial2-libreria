"""Tablas del módulo autores."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import LibroAutor


class Autor(SQLModel, table=True):
    __tablename__ = "autor"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=120)
    nacionalidad: str = Field(max_length=60)

    autorias: list["LibroAutor"] = Relationship(
        back_populates="autor", sa_relationship_kwargs={"lazy": "raise"}
    )
