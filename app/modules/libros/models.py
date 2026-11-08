"""Tablas del módulo libros: libro y libro_autor (objeto de asociación)."""

import app.core.metadata  # noqa: F401  (la convención de nombres debe existir antes de declarar tablas)

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Index, text
from sqlalchemy.sql.sqltypes import DateTime
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.modules.autores.models import Autor
    from app.modules.editoriales.models import Editorial
    from app.modules.generos.models import Genero
    from app.modules.usuarios.models import Usuario
    from app.modules.ventas.models import RenglonVenta, Venta


class Libro(SQLModel, table=True):
    """Libro. La FK vive del lado "muchos": muchos libros comparten editorial y género."""

    __tablename__ = "libro"
    __table_args__ = (
        CheckConstraint("precio > 0", name="precio_positivo"),
        CheckConstraint("stock >= 0", name="stock_no_negativo"),
        # El ISBN es único solo entre libros vigentes (no dados de baja).
        Index(
            "ix_libro_isbn_vigente",
            "isbn",
            unique=True,
            postgresql_where=text("borrado_en IS NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    isbn: str = Field(max_length=17)
    titulo: str = Field(max_length=255)
    precio: Decimal = Field(max_digits=10, decimal_places=2)
    stock: int
    editorial_id: int = Field(foreign_key="editorial.id", index=True)
    # genero_id admite NULL (agregación opcional); la 2ª migración lo agrega.
    genero_id: int | None = Field(default=None, foreign_key="genero.id", index=True)
    borrado_en: datetime | None = Field(default=None, sa_type=DateTime(timezone=True))

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
    movimientos: list["MovimientoStock"] = Relationship(
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


class MovimientoStock(SQLModel, table=True):
    """Movimiento de stock, de solo agregado (el trigger de la migración 0004 lo impone)."""

    __tablename__ = "movimiento_stock"
    __table_args__ = (CheckConstraint("cantidad <> 0", name="cantidad_no_cero"),)

    id: int | None = Field(default=None, primary_key=True)
    libro_id: int = Field(foreign_key="libro.id", index=True)
    venta_id: int | None = Field(default=None, foreign_key="venta.id", index=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    cantidad: int
    motivo: str = Field(max_length=120)
    cuando: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": text("now()")},
    )

    libro: "Libro" = Relationship(
        back_populates="movimientos", sa_relationship_kwargs={"lazy": "raise"}
    )
    venta: Optional["Venta"] = Relationship(
        back_populates="movimientos", sa_relationship_kwargs={"lazy": "raise"}
    )
    usuario: "Usuario" = Relationship(
        back_populates="movimientos", sa_relationship_kwargs={"lazy": "raise"}
    )
