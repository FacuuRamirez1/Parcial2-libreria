"""Tablas del módulo editoriales."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.libros.models import Libro


class Editorial(SQLModel, table=True):
    __tablename__ = "editorial"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=120, unique=True)
    pais: str = Field(max_length=60)

    libros: list["Libro"] = Relationship(
        back_populates="editorial", sa_relationship_kwargs={"lazy": "raise"}
    )
