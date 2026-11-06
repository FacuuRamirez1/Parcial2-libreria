"""Tablas del módulo libros: libro y libro_autor."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.ventas.models import RenglonVenta


class Libro(SQLModel, table=True):
    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="precio_positivo"),
        CheckConstraint("stock >= 0", name="stock_no_negativo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(max_length=17, unique=True)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    # --- genero (C-03: separable de la 1ª migración, D-10) ---
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True)
    genero: Optional["Genero"] = Relationship(
        back_populates="libros", sa_relationship_kwargs={"lazy": "raise"}
    )
    # --- fin genero ---

    editorial: "Editorial" = Relationship(
        back_populates="libros", sa_relationship_kwargs={"lazy": "raise"}
    )
    autorias: list["LibroAutor"] = Relationship(
        back_populates="libro",
        sa_relationship_kwargs={
            "lazy": "raise",
            "cascade": "all, delete-orphan",
            "order_by": "LibroAutor.orden",
        },
    )
    renglones: list["RenglonVenta"] = Relationship(
        back_populates="libro", sa_relationship_kwargs={"lazy": "raise"}
    )


class LibroAutor(SQLModel, table=True):
    __tablename__ = "libro_autor"
    __table_args__ = (
        CheckConstraint("orden >= 1", name="orden_positivo"),
        CheckConstraint(
            "rol IN ('autor', 'coautor', 'traductor', 'ilustrador')", name="rol_valido"
        ),
    )

    libro_id: int = Field(foreign_key="libro.id", primary_key=True)
    autor_id: int = Field(foreign_key="autor.id", primary_key=True, index=True)
    rol: str = Field(max_length=20)
    orden: int

    libro: "Libro" = Relationship(
        back_populates="autorias", sa_relationship_kwargs={"lazy": "raise"}
    )
    autor: "Autor" = Relationship(
        back_populates="autorias", sa_relationship_kwargs={"lazy": "raise"}
    )
