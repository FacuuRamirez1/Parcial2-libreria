"""Tablas del módulo libros: libro y libro_autor (objeto de asociación)."""

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
    """Libro. La FK vive del lado "muchos": muchos libros comparten editorial y género."""

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
    # genero_id admite NULL (agregación opcional); la 2ª migración lo agrega.
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True)

    editorial: "Editorial" = Relationship(
        back_populates="libros", sa_relationship_kwargs={"lazy": "raise"}
    )
    genero: Optional["Genero"] = Relationship(
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
    """Objeto de asociación libro-autor: el rol y el orden son de la relación."""

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
